import tkinter as tk
from tkinter import ttk, messagebox
from database import (
    init_db, validar_login, get_ultimas_cotizaciones,
    insertar_orden, get_ordenes_por_caja, get_cajas, actualizar_reales_orden
)
from numerical_entry import EntryNumerico
from formato_argentino import formato_argentino
from config import MONEDAS

MONEDAS_EXT = [m for m in MONEDAS if m != "ARS"]

class CajaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caja - Sistema Busta")
        self.geometry("900x850")
        
        self.usuario_actual = None
        self.caja_id = 1          # por ahora fijo, luego se puede elegir
        self.caja_nombre = "Caja 1"
        self.mostrar_login()

    # ---------- Login ----------
    def mostrar_login(self):
        for widget in self.winfo_children():
            widget.destroy()
        tk.Label(self, text="Usuario:").pack(pady=5)
        self.entry_user = tk.Entry(self)
        self.entry_user.pack(pady=5)
        tk.Label(self, text="Contraseña:").pack(pady=5)
        self.entry_pass = tk.Entry(self, show="*")
        self.entry_pass.pack(pady=5)
        tk.Button(self, text="Ingresar", command=self.login).pack(pady=10)

    def login(self):
        nombre = self.entry_user.get()
        password = self.entry_pass.get()
        user = validar_login(nombre, password)
        if user:
            self.usuario_actual = user
            # En CajaApp, cualquier usuario puede operar (admin o cajero)
            self.iniciar_caja()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    # ---------- Interfaz de caja (ventana principal) ----------
    def iniciar_caja(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.geometry("900x850")
        self.tipo_var = tk.StringVar(value='venta')
        # Obtener nombre real de la caja desde la BD
        cajas = get_cajas()
        for c in cajas:
            if c[0] == self.caja_id:
                self.caja_nombre = c[1]
                break

        # Título de la caja
        tk.Label(self, text=self.caja_nombre, font=('Arial', 12)).pack(pady=5)

        # Cotizaciones de referencia
        frame_ref = tk.LabelFrame(self, text="Cotizaciones")
        frame_ref.pack(fill='x', padx=10, pady=5)
        self.actualizar_vista_cotizaciones(frame_ref)

        # Label grande de tipo de operación
        self.lbl_tipo_operacion = tk.Label(self, text="VENTA", font=('Arial', 16, 'bold'), fg='green')
        self.lbl_tipo_operacion.pack(pady=(5, 0))

        # Formulario
        form_frame = tk.LabelFrame(self, text="Nueva operación")
        form_frame.pack(fill='x', padx=10, pady=5)

        self.monto_rec_calc = None
        self.monto_ent_calc = None

        # --- Formulario (cada fila es un Frame) ---
        # Fila 0: Tipo
        fila0 = tk.Frame(form_frame)
        fila0.pack(fill='x', pady=5)
        tk.Label(fila0, text="Tipo:").pack(side='left', padx=5)
        tipo_frame = tk.Frame(fila0)
        tipo_frame.pack(side='left', padx=5)
        self.btn_venta = tk.Button(tipo_frame, text="VENTA", font=('Arial', 10, 'bold'),
                                   bg='#e6ffe6', fg='green', width=10,
                                   command=self.seleccionar_venta)
        self.btn_venta.pack(side='left', padx=12)
        self.btn_compra = tk.Button(tipo_frame, text="COMPRA", font=('Arial', 10),
                                    bg='#f0f0f0', fg='black', width=10,
                                    command=self.seleccionar_compra)
        self.btn_compra.pack(side='left', padx=20)

        # Fila 1: Moneda
        fila1 = tk.Frame(form_frame)
        fila1.pack(fill='x', pady=5)
        tk.Label(fila1, text="Moneda:").pack(side='left', padx=5)
        self.moneda_ref_var = tk.StringVar(value='USD')
        moneda_ref_combo = ttk.Combobox(fila1, textvariable=self.moneda_ref_var,
                                        values=MONEDAS_EXT, state='readonly', width=6)
        moneda_ref_combo.pack(side='left', padx=5)
        moneda_ref_combo.bind('<<ComboboxSelected>>', lambda e: self.actualizar_labels())

        # Fila 2: Cotización
        fila2 = tk.Frame(form_frame)
        fila2.pack(fill='x', pady=5)
        tk.Label(fila2, text="Cotización:").pack(side='left', padx=5)
        self.cotizacion_entry = EntryNumerico(fila2, width=12)
        self.cotizacion_entry.pack(side='left', padx=5)

        self.btn_sugerida = tk.Button(fila2, text="Usar sugerida", command=self.usar_cotizacion_sugerida)
        self.btn_sugerida.pack(side='left', padx=5)

        # Fila 3: Recibí
        fila3 = tk.Frame(form_frame)
        fila3.pack(fill='x', pady=5)
        self.lbl_recibido = tk.Label(fila3, text="Recibí (ARS):")
        self.lbl_recibido.pack(side='left', padx=5)
        self.monto_recibido_entry = EntryNumerico(fila3, width=12)
        self.monto_recibido_entry.pack(side='left', padx=5)

        # Fila 4: Debería dar
        fila4 = tk.Frame(form_frame)
        fila4.pack(fill='x', pady=5)
        self.lbl_deberia = tk.Label(fila4, text="Debería dar (USD):")
        self.lbl_deberia.pack(side='left', padx=5)
        self.monto_deberia_var = tk.StringVar(value="")
        tk.Entry(fila4, textvariable=self.monto_deberia_var, state='readonly', width=12).pack(side='left', padx=5)
        
        self.btn_calcular = tk.Button(fila4, text="Calcular", command=self.calcular_deberia)
        self.btn_calcular.pack(side='left', padx=5)

        # Fila 5: Dio efectivamente
        fila5 = tk.Frame(form_frame)
        fila5.pack(fill='x', pady=5)
        self.lbl_dio = tk.Label(fila5, text="Dio efectivamente (USD):")
        self.lbl_dio.pack(side='left', padx=5)
        self.monto_dio_entry = EntryNumerico(fila5, width=12)
        self.monto_dio_entry.pack(side='left', padx=5)
        
        self.btn_usar_calculado = tk.Button(fila5, text="Usar calculado", command=self.usar_calculado)
        self.btn_usar_calculado.pack(side='left', padx=5)

        # Fila 6: Cliente
        fila6 = tk.Frame(form_frame)
        fila6.pack(fill='x', pady=5)
        tk.Label(fila6, text="Cliente:").pack(side='left', padx=5)
        self.cliente_entry = tk.Entry(fila6, width=20)
        self.cliente_entry.pack(side='left', padx=5)

        # Fila 7: Pendiente
        fila7 = tk.Frame(form_frame)
        fila7.pack(fill='x', pady=5)
        self.pendiente_var = tk.BooleanVar(value=False)
        
        self.chk_pendiente = tk.Checkbutton(fila7, text="Dejar pendiente", variable=self.pendiente_var)
        self.chk_pendiente.pack(side='left', padx=5)

        # Fila 8: Guardar
        fila8 = tk.Frame(form_frame)
        fila8.pack(fill='x', pady=5)
        self.btn_guardar = tk.Button(fila8, text="Guardar operación", command=self.guardar_operacion)
        self.btn_guardar.pack(side='left', padx=45)


        # --- Bindeos de teclado (Enter) ---
        self.btn_venta.bind('<Return>', lambda e: self.seleccionar_venta())
        self.btn_compra.bind('<Return>', lambda e: self.seleccionar_compra())
        self.btn_sugerida.bind('<Return>', lambda e: self.usar_cotizacion_sugerida())
        self.btn_calcular.bind('<Return>', lambda e: self.calcular_deberia())
        self.btn_usar_calculado.bind('<Return>', lambda e: self.usar_calculado())
        self.chk_pendiente.bind('<Return>', lambda e: self.pendiente_var.set(not self.pendiente_var.get()))
        self.btn_guardar.bind('<Return>', lambda e: self.guardar_operacion())
        # Fila de diferencia (puede quedar vacía)
        fila_diff = tk.Frame(form_frame)
        fila_diff.pack(fill='x', pady=2)
        self.lbl_diferencia = tk.Label(fila_diff, text="", fg="red")
        self.lbl_diferencia.pack(side='left', padx=5)
        # ========== FIN FORMULARIO CORREGIDO ==========

        # ---- Tabla de órdenes de la caja ----
        ordenes_frame = tk.LabelFrame(self, text="Operaciones en esta caja (doble clic para editar)")
        ordenes_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.filtro_frame = tk.Frame(ordenes_frame)
        self.filtro_frame.pack(fill='x', padx=5, pady=5)
        self.solo_pendientes_var = tk.BooleanVar()
        tk.Checkbutton(self.filtro_frame, text="Ver solo pendientes", variable=self.solo_pendientes_var,
                       command=self.actualizar_tabla_caja).pack(side='left')

        self.actualizar_labels()
        self.actualizar_tabla_caja()

        # Botón Cerrar sesión
        tk.Button(self, text="Cerrar sesión", command=self.cerrar_sesion).pack(pady=10)

    # ---------- Métodos de la caja ----------
    def seleccionar_venta(self):
        self.tipo_var.set('venta')
        self.btn_venta.config(bg='#e6ffe6', fg='green', font=('Arial', 10, 'bold'))
        self.btn_compra.config(bg='#f0f0f0', fg='black', font=('Arial', 10))
        self.actualizar_labels()

    def seleccionar_compra(self):
        self.tipo_var.set('compra')
        self.btn_compra.config(bg='#e6f0ff', fg='blue', font=('Arial', 10, 'bold'))
        self.btn_venta.config(bg='#f0f0f0', fg='black', font=('Arial', 10))
        self.actualizar_labels()

    def usar_cotizacion_sugerida(self):
        tipo = self.tipo_var.get()
        moneda = self.moneda_ref_var.get()
        datos = get_ultimas_cotizaciones()
        par = f"{moneda}/ARS"
        if par in datos:
            info = datos[par]
            cot = info.get(tipo)
            if cot is not None and cot != 0:
                self.cotizacion_entry.set_value(cot)
            else:
                messagebox.showwarning("Sin datos", f"No hay cotización de {tipo} para {par}")
        else:
            par = f"ARS/{moneda}"
            if par in datos:
                info = datos[par]
                cot = info.get(tipo)
                if cot is not None and cot != 0:
                    self.cotizacion_entry.set_value(cot)
                else:
                    messagebox.showwarning("Sin datos", f"No hay cotización de {tipo} para {par}")
            else:
                messagebox.showwarning("Sin datos", "No se encontraron cotizaciones para este par")

    def actualizar_labels(self):
        tipo = self.tipo_var.get()
        moneda_ref = self.moneda_ref_var.get()
        if tipo == 'venta':
            self.lbl_tipo_operacion.config(text="VENTA", fg='green')
            self.lbl_recibido.config(text=f"Recibí (ARS):")
            self.lbl_deberia.config(text=f"Debería dar ({moneda_ref}):")
            self.lbl_dio.config(text=f"Dio efectivamente ({moneda_ref}):")
        else:
            self.lbl_tipo_operacion.config(text="COMPRA", fg='blue')
            self.lbl_recibido.config(text=f"Recibí ({moneda_ref}):")
            self.lbl_deberia.config(text="Debería dar (ARS):")
            self.lbl_dio.config(text="Dio efectivamente (ARS):")

    def calcular_deberia(self):
        cot = self.cotizacion_entry.get_value()
        if cot <= 0:
            messagebox.showerror("Error", "Ingresá una cotización válida")
            return
        tipo = self.tipo_var.get()
        monto_rec = self.monto_recibido_entry.get_value()
        if monto_rec <= 0:
            messagebox.showwarning("Atención", "Ingresá el monto que dio el cliente")
            return
        if tipo == 'venta':
            monto_deberia = monto_rec / cot
        else:
            monto_deberia = monto_rec * cot
        self.monto_deberia_var.set(formato_argentino(monto_deberia, 6))
        self.monto_rec_calc = monto_rec
        self.monto_ent_calc = monto_deberia
        self.lbl_diferencia.config(text="")

    def usar_calculado(self):
        if self.monto_ent_calc is not None:
            self.monto_dio_entry.set_value(self.monto_ent_calc, 6)
            self.lbl_diferencia.config(text="")

    def actualizar_diferencia(self):
        if self.monto_ent_calc is None:
            return
        
        dio = self.monto_dio_entry.get_value()
        if dio == 0.0 and self.monto_dio_entry.get().strip() == "":
            self.lbl_diferencia.config(text="")
            return
        dif = dio - self.monto_ent_calc
        if abs(dif) > 0.009:
            self.lbl_diferencia.config(text=f"Diferencia: {formato_argentino(dif)} (faltante si es negativo)")
        else:
            self.lbl_diferencia.config(text="")

    def guardar_operacion(self):


        tipo = self.tipo_var.get()
        moneda_ref = self.moneda_ref_var.get()
        monto_rec = self.monto_recibido_entry.get_value()
        if monto_rec <= 0:
            messagebox.showerror("Error", "Completá el monto recibido")
            return
        if self.monto_ent_calc is None:
            messagebox.showerror("Error", "Primero presioná 'Calcular'")
            return
        
        monto_dio = self.monto_dio_entry.get_value()
        if monto_dio == 0.0 and self.monto_dio_entry.get().strip() == "":
            messagebox.showerror("Error", "Ingresá cuánto diste efectivamente")
            return
        
        cot = self.cotizacion_entry.get_value()
        if cot <= 0:
            messagebox.showerror("Error", "Cotización inválida")
            return
        cliente = self.cliente_entry.get().strip()
        estado = 'pendiente' if self.pendiente_var.get() else 'completada'

        if tipo == 'venta':
            moneda_recibida = 'ARS'
            moneda_entregada = moneda_ref
        else:
            moneda_recibida = moneda_ref
            moneda_entregada = 'ARS'

        insertar_orden(tipo, moneda_recibida, monto_rec, monto_rec,
                       moneda_entregada, self.monto_ent_calc, monto_dio,
                       cot, cliente, estado, self.caja_id, self.usuario_actual['id'])

        messagebox.showinfo("Éxito", "Operación registrada.", parent=self)

        # Limpiar formulario
       
        self.cotizacion_entry.delete(0, tk.END)
        self.monto_recibido_entry.delete(0, tk.END)
        self.monto_deberia_var.set("")
        self.monto_dio_entry.delete(0, tk.END)
        self.cliente_entry.delete(0, tk.END)
        self.monto_rec_calc = None
        self.monto_ent_calc = None
        self.pendiente_var.set(False)
        self.lbl_diferencia.config(text="")
        self.actualizar_tabla_caja()

    def actualizar_tabla_caja(self):
        # Buscar el ordenes_frame
        for child in self.winfo_children():
            if isinstance(child, tk.LabelFrame) and 'Operaciones' in child.cget('text'):
                ordenes_frame = child
                break
        else:
            return

        # Destruir todo menos el filtro
        for w in ordenes_frame.winfo_children():
            if w != self.filtro_frame:
                w.destroy()

        solo_pend = self.solo_pendientes_var.get()
        ordenes = get_ordenes_por_caja(caja_id=self.caja_id, limite=50, solo_pendientes=solo_pend)

        columnas = ['ID', 'Fecha', 'Tipo', 'Recibido', 'Entregado', 'Cotización', 'Deuda', 'Estado', 'Cliente']
        tree = ttk.Treeview(ordenes_frame, columns=columnas, show='headings', height=10)
        
        tree.heading('ID', text='ID')
        tree.heading('Fecha', text='Fecha')
        tree.heading('Tipo', text='Tipo')
        tree.heading('Recibido', text='Recibido')
        tree.heading('Entregado', text='Entregado')
        tree.heading('Cotización', text='Cotización')
        tree.heading('Deuda', text='Deuda')
        tree.heading('Estado', text='Estado')
        tree.heading('Cliente', text='Cliente')

        tree.column('ID', width=40)
        tree.column('Fecha', width=120)
        tree.column('Tipo', width=60)
        tree.column('Recibido', width=140)
        tree.column('Entregado', width=140)
        tree.column('Cotización', width=80)
        tree.column('Deuda', width=80)
        tree.column('Estado', width=80)
        tree.column('Cliente', width=120)

        for o in ordenes:
            recibido = f"{o[3]} {formato_argentino(o[5])}" if o[5] is not None else f"{o[3]} 0"
            entregado = f"{o[6]} {formato_argentino(o[8])}" if o[8] is not None else f"{o[6]} 0"
            deuda = ""
            if o[11] == 'pendiente' and o[7] is not None and o[8] is not None:
                falta = o[7] - o[8]
                if falta > 0.001:
                    deuda = f"{o[6]} {formato_argentino(falta)}"
                elif falta < -0.001:
                    deuda = f"{o[6]} sobra {formato_argentino(-falta)}"
            cot_str = formato_argentino(o[9]) if o[9] else "—"
            tree.insert('', 'end', values=(o[0], o[1], o[2], recibido, entregado, cot_str, deuda, o[11], o[10] or ""), tags=(o[11],))

            
        tree.tag_configure('pendiente', background='#fff3cd')
        tree.tag_configure('completada', background='#d4edda')
        tree.pack(fill='both', expand=True)

        # Doble clic para editar
        tree.bind("<Double-1>", lambda event: self.editar_orden_desde_tabla(event, tree))

    def editar_orden_desde_tabla(self, event, tree):
        selected = tree.selection()
        if not selected:
            return
        item = tree.item(selected[0])
        id_orden = item['values'][0]
        ordenes = get_ordenes_por_caja(caja_id=self.caja_id, limite=1000)
        orden_data = None
        for o in ordenes:
            if o[0] == id_orden:
                orden_data = o
                break
        if orden_data:
            self.abrir_editor_orden(orden_data)

    def abrir_editor_orden(self, orden):
        id_orden = orden[0]
        moneda_rec = orden[3]
        moneda_ent = orden[6]
        rec_calc = orden[4]
        rec_real = orden[5]
        ent_calc = orden[7]
        ent_real = orden[8]
        estado_actual = orden[11]

        editor = tk.Toplevel(self)
        editor.title(f"Orden {id_orden} – Gestionar entregas")
        editor.geometry("500x550")

        # Título destacado: tipo de operación
        tipo_operacion = orden[2].capitalize()
        tk.Label(editor, text=f"{tipo_operacion}", font=('Arial', 14, 'bold')).pack(pady=5)

        # Línea secundaria
        nombre_caja = orden[12]
        texto_secundario = f"Caja: {nombre_caja}  |  Cotización: {formato_argentino(orden[9])}  |  Cliente: {orden[10] or '-'}  |  ID: #{id_orden}"
        tk.Label(editor, text=texto_secundario, font=('Arial', 10)).pack(pady=2)

        # Frame resumen
        resumen_frame = tk.LabelFrame(editor, text="Resumen de la operación")
        resumen_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(resumen_frame, text=f"Cliente dio:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        tk.Label(resumen_frame, text=f"{moneda_rec} {formato_argentino(rec_real)}").grid(row=0, column=1, padx=5, pady=2, sticky='w')

        tk.Label(resumen_frame, text=f"Cajero debe dar:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        tk.Label(resumen_frame, text=f"{moneda_ent} {formato_argentino(ent_calc, 6)}").grid(row=1, column=1, padx=5, pady=2, sticky='w')

        tk.Label(resumen_frame, text=f"Entregado hasta ahora:").grid(row=2, column=0, padx=5, pady=2, sticky='w')
        tk.Label(resumen_frame, text=f"{moneda_ent} {formato_argentino(ent_real)}").grid(row=2, column=1, padx=5, pady=2, sticky='w')

        # Deuda
        deuda_actual = ent_calc - ent_real
        deuda_str = formato_argentino(abs(deuda_actual), 6) if abs(deuda_actual) > 0.001 else "Saldado"
        deuda_label = tk.Label(resumen_frame, text="Deuda pendiente:", fg="red" if abs(deuda_actual) > 0.001 else "green")
        deuda_label.grid(row=3, column=0, padx=5, pady=2, sticky='w')
        deuda_valor_label = tk.Label(resumen_frame, text=f"{moneda_ent} {deuda_str}", fg="red" if abs(deuda_actual) > 0.001 else "green")
        deuda_valor_label.grid(row=3, column=1, padx=5, pady=2, sticky='w')

        # Frame nueva entrega
        entrega_frame = tk.LabelFrame(editor, text="Nueva entrega (agrega a lo ya entregado)")
        entrega_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(entrega_frame, text=f"Monto a entregar ahora ({moneda_ent}):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        nueva_entrega_entry = EntryNumerico(entrega_frame, width=12)
        nueva_entrega_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(entrega_frame, text="(se sumará al real actual)").grid(row=0, column=2, padx=5, pady=5, sticky='w')

        def agregar_entrega():
            monto = nueva_entrega_entry.get_value()
            if monto <= 0:
                messagebox.showerror("Error", "Ingresá un monto positivo")
                return
            nuevo_real = ent_real + monto
            actualizar_reales_orden(id_orden, rec_real, nuevo_real, None)
            editor.destroy()
            # Reabrir con datos frescos
            orden_actualizada = get_ordenes_por_caja(caja_id=self.caja_id, limite=1000)
            for o in orden_actualizada:
                if o[0] == id_orden:
                    self.abrir_editor_orden(o)
                    break
            self.actualizar_tabla_caja()

        tk.Button(entrega_frame, text="Agregar entrega", command=agregar_entrega).grid(row=1, column=0, columnspan=2, pady=5)

        # Botón entregar total
        def entregar_total():
            actualizar_reales_orden(id_orden, rec_real, ent_calc, 'completada')
            messagebox.showinfo("Saldado", "Deuda saldada, orden completada.")
            editor.destroy()
            self.actualizar_tabla_caja()

        tk.Button(editor, text="Entregar total (saldar deuda)", command=entregar_total).pack(pady=5)

        # Campos de edición directa
        edit_frame = tk.LabelFrame(editor, text="Edición directa de reales (uso excepcional)")
        edit_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(edit_frame, text="Recibido real:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        entry_rec_real = tk.Entry(edit_frame, width=12)
        entry_rec_real.insert(0, formato_argentino(rec_real))
        entry_rec_real.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(edit_frame, text="Entregado real:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        entry_ent_real = tk.Entry(edit_frame, width=12)
        entry_ent_real.insert(0, formato_argentino(ent_real))
        entry_ent_real.grid(row=1, column=1, padx=5, pady=5)

        # Estado
        tk.Label(edit_frame, text="Estado:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        estado_var = tk.StringVar(value=estado_actual)
        ttk.Combobox(edit_frame, textvariable=estado_var, values=['pendiente', 'completada'], state='readonly').grid(row=2, column=1, padx=5, pady=5)

        def guardar_cambios_directos():
            try:
                # Usar get_value para interpretar comas y puntos
                nuevo_rec = EntryNumerico.get_value_from_text(entry_rec_real.get())
                nuevo_ent = EntryNumerico.get_value_from_text(entry_ent_real.get())
            except ValueError:
                messagebox.showerror("Error", "Valores numéricos inválidos")
                return
            actualizar_reales_orden(id_orden, nuevo_rec, nuevo_ent, estado_var.get())
            messagebox.showinfo("Guardado", "Cambios aplicados.")
            editor.destroy()
            self.actualizar_tabla_caja()

        tk.Button(edit_frame, text="Guardar cambios", command=guardar_cambios_directos).grid(row=3, column=0, columnspan=2, pady=5)

        # Actualizar deuda visual al modificar reales directamente
        def actualizar_deuda_visual(*args):
            try:
                rec = EntryNumerico.get_value_from_text(entry_rec_real.get())
                ent = EntryNumerico.get_value_from_text(entry_ent_real.get())
            except:
                return
            deuda = ent_calc - ent
            deuda_str = formato_argentino(abs(deuda), 6) if abs(deuda) > 0.001 else "Saldado"
            deuda_valor_label.config(text=f"{moneda_ent} {deuda_str}")

        entry_ent_real.bind('<KeyRelease>', actualizar_deuda_visual)
        entry_rec_real.bind('<KeyRelease>', actualizar_deuda_visual)

        tk.Button(editor, text="Cerrar", command=editor.destroy).pack(pady=5)

    def actualizar_vista_cotizaciones(self, frame):
        for w in frame.winfo_children():
            w.destroy()
        datos = get_ultimas_cotizaciones()
        columnas = ['Par', 'Compra', 'Venta', 'Actualización']
        tree = ttk.Treeview(frame, columns=columnas, show='headings', height=6)
        for col in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col != 'Actualización' else 150)
        for par, info in datos.items():
            compra = f"{info['cotizacion']} {formato_argentino(info['compra'])}" if info['compra'] else "—"
            venta = f"{info['cotizacion']} {formato_argentino(info['venta'])}" if info['venta'] else "—"
            tree.insert('', 'end', values=(par, compra, venta, info['fecha']))
        tree.pack(fill='both', expand=True)

    # ---------- Utilidades ----------
    def limpiar_ventana(self):
        for widget in self.winfo_children():
            widget.destroy()

    def cerrar_sesion(self):
        self.usuario_actual = None
        self.mostrar_login()

if __name__ == '__main__':
    init_db()
    app = CajaApp()
    app.mainloop()