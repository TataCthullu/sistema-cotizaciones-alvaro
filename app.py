import tkinter as tk
from tkinter import ttk, messagebox
from database import (
    init_db, validar_login, insertar_cotizacion, get_ultimas_cotizaciones,
    insertar_orden, get_ordenes_por_caja, get_cajas, actualizar_reales_orden, get_historial_cotizaciones
)
#from excel_handler import actualizar_precio_en_todos
from config import MONEDAS

MONEDAS_EXT = [m for m in MONEDAS if m != "ARS"]

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Cotizaciones - Álvaro")
        self.geometry("1000x750")
        self.usuario_actual = None
        # Filtros del admin
        self.filtro_caja_id = tk.IntVar(value=0)  # 0 = todas
        self.filtro_tipo = tk.StringVar(value='')
        self.filtro_estado = tk.StringVar(value='')
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
            if user['rol'] == 'admin':
                self.mostrar_panel_admin()
            else:
                self.mostrar_panel_cajero()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    # ---------- Panel Admin ----------
    def mostrar_panel_admin(self):
        self.limpiar_ventana()
        self.geometry("1000x750")
        tk.Label(self, text=f"Panel Administrador",
                 font=('Arial', 14)).pack(pady=5)

        # Pestañas de cotizaciones
        notebook_cot = ttk.Notebook(self)
        notebook_cot.pack(fill='x', padx=10, pady=5)

        tab_actuales = tk.Frame(notebook_cot)
        notebook_cot.add(tab_actuales, text="Cotizaciones actuales")
        self.actualizar_vista_cotizaciones(tab_actuales)

        tab_historial = tk.Frame(notebook_cot)
        notebook_cot.add(tab_historial, text="Historial de cotizaciones")
        self.actualizar_historial_cotizaciones(tab_historial)

        frame_cajas = tk.LabelFrame(self, text="Cajas")
        frame_cajas.pack(fill='x', padx=10, pady=5)
        cajas = get_cajas()
        for caja in cajas:
            btn = tk.Button(frame_cajas, text=caja[1],
                            command=lambda c=caja: self.abrir_caja(c[0], c[1]))
            btn.pack(side='left', padx=10, pady=5)


        # --- Panel de filtros ---
        filtros_frame = tk.LabelFrame(self, text="Filtros de órdenes")
        filtros_frame.pack(fill='x', padx=10, pady=5)

        # Filtro por caja
        tk.Label(filtros_frame, text="Caja:").pack(side='left', padx=5)
        self.botones_caja_filtro = []
        btn_todas = tk.Button(filtros_frame, text="Todas", relief='raised', bg='#4CAF50',
                              command=lambda: self.toggle_filtro_caja(0))
        btn_todas.pack(side='left', padx=2)
        self.botones_caja_filtro.append(btn_todas)

        cajas = get_cajas()
        for caja in cajas:
            btn = tk.Button(filtros_frame, text=caja[1], relief='raised', bg='#f0f0f0',
                            command=lambda c=caja: self.toggle_filtro_caja(c[0]))
            btn.pack(side='left', padx=2)
            self.botones_caja_filtro.append(btn)

        # Separador
        tk.Label(filtros_frame, text="  |  ").pack(side='left')

        # Filtro por tipo
        tk.Label(filtros_frame, text="Tipo:").pack(side='left', padx=5)
        self.botones_tipo_filtro = []
        for tipo, texto in [('', 'Todas'), ('compra', 'Compra'), ('venta', 'Venta')]:
            btn = tk.Button(filtros_frame, text=texto, relief='raised', bg='#4CAF50' if tipo=='' else '#f0f0f0',
                            command=lambda t=tipo: self.toggle_filtro_tipo(t))
            btn.pack(side='left', padx=2)
            self.botones_tipo_filtro.append(btn)

        # Separador
        tk.Label(filtros_frame, text="  |  ").pack(side='left')

        # Filtro por estado
        tk.Label(filtros_frame, text="Estado:").pack(side='left', padx=5)
        self.botones_estado_filtro = []
        for estado, texto in [('', 'Todos'), ('pendiente', 'Pendiente'), ('completada', 'Completada')]:
            btn = tk.Button(filtros_frame, text=texto, relief='raised', bg='#4CAF50' if estado=='' else '#f0f0f0',
                            command=lambda e=estado: self.toggle_filtro_estado(e))
            btn.pack(side='left', padx=2)
            self.botones_estado_filtro.append(btn)


        frame_ordenes = tk.LabelFrame(self, text="Todas las órdenes")
        frame_ordenes.pack(fill='both', expand=True, padx=10, pady=5)
        self.actualizar_vista_ordenes_general(frame_ordenes)

        # Frame superior para Nueva Cotización
        btn_frame_top = tk.Frame(self)
        btn_frame_top.pack(pady=(10, 0))
        tk.Button(btn_frame_top, text="Nueva Cotización", command=self.abrir_form_cotizacion).pack(side='left', padx=5)

        # Frame inferior para Cerrar sesión, anclado abajo a la izquierda
        btn_frame_bottom = tk.Frame(self)
        btn_frame_bottom.pack(side='bottom', anchor='w', pady=10, padx=10)
        tk.Button(btn_frame_bottom, text="Cerrar sesión", command=self.cerrar_sesion).pack()

    # ---------- Panel Cajero ----------
    def mostrar_panel_cajero(self):
        self.limpiar_ventana()
        self.geometry("1000x750")
        tk.Label(self, text=f"Panel Cajero - {self.usuario_actual['id']}",
                 font=('Arial', 14)).pack(pady=5)

        frame_cot = tk.LabelFrame(self, text="Cotizaciones actuales")
        frame_cot.pack(fill='x', padx=10, pady=5)
        self.actualizar_vista_cotizaciones(frame_cot)

        frame_ordenes = tk.LabelFrame(self, text="Últimas órdenes")
        frame_ordenes.pack(fill='both', expand=True, padx=10, pady=5)
        self.actualizar_vista_ordenes_general(frame_ordenes)

        tk.Button(self, text="Cerrar sesión", command=self.cerrar_sesion).pack(pady=10)

    # ---------- Cotizaciones ----------
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
            compra = f"{info['cotizacion']} {info['compra']:.2f}" if info['compra'] else "—"
            venta = f"{info['cotizacion']} {info['venta']:.2f}" if info['venta'] else "—"
            tree.insert('', 'end', values=(par, compra, venta, info['fecha']))
        tree.pack(fill='both', expand=True)

    def actualizar_historial_cotizaciones(self, frame):
        for w in frame.winfo_children():
            w.destroy()
        historial = get_historial_cotizaciones(limite=100)
        columnas = ['ID', 'Fecha', 'Par', 'Compra', 'Venta']
        tree = ttk.Treeview(frame, columns=columnas, show='headings', height=10)
        tree.heading('ID', text='ID')
        tree.heading('Fecha', text='Fecha')
        tree.heading('Par', text='Par')
        tree.heading('Compra', text='Compra')
        tree.heading('Venta', text='Venta')
        tree.column('ID', width=40)
        tree.column('Fecha', width=150)
        tree.column('Par', width=100)
        tree.column('Compra', width=120)
        tree.column('Venta', width=120)

        for cot in historial:
            par = f"{cot[2]}/{cot[3]}"
            compra = f"{cot[3]} {cot[4]:.2f}" if cot[4] else "—"
            venta = f"{cot[3]} {cot[5]:.2f}" if cot[5] else "—"
            tree.insert('', 'end', values=(cot[0], cot[1], par, compra, venta))
        tree.pack(fill='both', expand=True)

    # ---------- Tabla general de órdenes (limpia) ----------
    def actualizar_vista_ordenes_general(self, frame):
        for w in frame.winfo_children():
            w.destroy()
        caja_id = self.filtro_caja_id.get() if self.filtro_caja_id.get() != 0 else None
        tipo_op = self.filtro_tipo.get() if self.filtro_tipo.get() else None
        estado = self.filtro_estado.get() if self.filtro_estado.get() else None
        ordenes = get_ordenes_por_caja(caja_id=caja_id, limite=50, tipo_operacion=tipo_op, estado=estado)
        columnas = ['ID', 'Fecha', 'Tipo', 'Recibido', 'Entregado', 'Deuda', 'Estado']
        tree = ttk.Treeview(frame, columns=columnas, show='headings', height=10)
        tree.heading('ID', text='ID')
        tree.heading('Fecha', text='Fecha')
        tree.heading('Tipo', text='Tipo')
        tree.heading('Recibido', text='Recibido')
        tree.heading('Entregado', text='Entregado')
        tree.heading('Deuda', text='Deuda')
        tree.heading('Estado', text='Estado')
        tree.column('ID', width=40)
        tree.column('Fecha', width=120)
        tree.column('Tipo', width=60)
        tree.column('Recibido', width=140)
        tree.column('Entregado', width=140)
        tree.column('Deuda', width=100)
        tree.column('Estado', width=80)

        for o in ordenes:
            recibido = f"{o[3]} {o[5]:.2f}" if o[5] is not None else f"{o[3]} 0.00"
            entregado = f"{o[6]} {o[8]:.2f}" if o[8] is not None else f"{o[6]} 0.00"
            # Deuda con moneda
            deuda = ""
            if o[11] == 'pendiente' and o[7] is not None and o[8] is not None:
                falta = o[7] - o[8]   # calculado - real
                if falta > 0.001:
                    deuda = f"{o[6]} {falta:.2f}"      # ej. "USD 6.50"
                
            tree.insert('', 'end', values=(o[0], o[1], o[2], recibido, entregado, deuda, o[11]),
                        tags=(o[11],))
        tree.tag_configure('pendiente', background='#fff3cd')
        tree.tag_configure('completada', background='#d4edda')
        tree.pack(fill='both', expand=True)

    # ---------- Ventana de Caja ----------
    def abrir_caja(self, caja_id, caja_nombre):
        ventana = tk.Toplevel(self)
        ventana.title(f"{caja_nombre} - Operación")
        ventana.geometry("900x700")
        ventana.caja_id = caja_id

        tk.Label(ventana, text=f"{caja_nombre} - Cotizaciones de referencia", font=('Arial', 12)).pack(pady=5)
        frame_ref = tk.LabelFrame(ventana, text="Cotizaciones")
        frame_ref.pack(fill='x', padx=10, pady=5)
        self.actualizar_vista_cotizaciones(frame_ref)

        # Formulario
        form_frame = tk.LabelFrame(ventana, text="Nueva operación")
        form_frame.pack(fill='x', padx=10, pady=5)

        # Variables de cálculo
        self.monto_rec_calc = None
        self.monto_ent_calc = None

        # Fila 0: Tipo
        tk.Label(form_frame, text="Tipo:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.tipo_var = tk.StringVar(value='venta')
        ttk.Combobox(form_frame, textvariable=self.tipo_var, values=['compra', 'venta'],
                     state='readonly', width=10).grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.tipo_var.trace('w', lambda *a: self.actualizar_labels())

        # Fila 1: Moneda
        tk.Label(form_frame, text="Moneda:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.moneda_ref_var = tk.StringVar(value='USD')
        moneda_ref_combo = ttk.Combobox(form_frame, textvariable=self.moneda_ref_var,
                                        values=MONEDAS_EXT, state='readonly', width=6)
        moneda_ref_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        moneda_ref_combo.bind('<<ComboboxSelected>>', lambda e: self.actualizar_labels())

        # Fila 2: Cotización
        tk.Label(form_frame, text="Cotización:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.cotizacion_entry = tk.Entry(form_frame, width=12)
        self.cotizacion_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        tk.Button(form_frame, text="Usar sugerida", command=self.usar_cotizacion_sugerida).grid(row=2, column=3, padx=5, pady=5)

        # Fila 3: Recibí (cliente da)
        self.lbl_recibido = tk.Label(form_frame, text="Recibí (cliente da ARS):")
        self.lbl_recibido.grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.moneda_recibida_var = tk.StringVar(value='ARS')
        tk.Label(form_frame, textvariable=self.moneda_recibida_var, width=6).grid(row=3, column=1, padx=5, pady=5)
        self.monto_recibido_entry = tk.Entry(form_frame, width=12)
        self.monto_recibido_entry.grid(row=3, column=2, padx=5, pady=5)

        # Fila 4: Debería dar (cajero) – calculado
        self.lbl_deberia = tk.Label(form_frame, text="Debería dar (cajero USD):")
        self.lbl_deberia.grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.moneda_entregada_var = tk.StringVar(value='USD')
        tk.Label(form_frame, textvariable=self.moneda_entregada_var, width=6).grid(row=4, column=1, padx=5, pady=5)
        self.monto_deberia_var = tk.StringVar(value="")
        tk.Entry(form_frame, textvariable=self.monto_deberia_var, state='readonly', width=12).grid(row=4, column=2, padx=5, pady=5)
        tk.Button(form_frame, text="Calcular", command=self.calcular_deberia).grid(row=4, column=3, padx=5, pady=5)

        # Fila 5: Dio efectivamente (cajero) – manual
        self.lbl_dio = tk.Label(form_frame, text="Dio efectivamente (cajero USD):")
        self.lbl_dio.grid(row=5, column=0, padx=5, pady=5, sticky='w')
        tk.Label(form_frame, textvariable=self.moneda_entregada_var, width=6).grid(row=5, column=1, padx=5, pady=5)
        self.monto_dio_entry = tk.Entry(form_frame, width=12)
        self.monto_dio_entry.grid(row=5, column=2, padx=5, pady=5)
        tk.Button(form_frame, text="Usar calculado", command=self.usar_calculado).grid(row=5, column=3, padx=5, pady=5)

        # Fila 6: Diferencia
        self.lbl_diferencia = tk.Label(form_frame, text="", fg="red")
        self.lbl_diferencia.grid(row=6, column=0, columnspan=4, pady=5)

        # Fila 7: Cliente
        tk.Label(form_frame, text="Cliente:").grid(row=7, column=0, padx=5, pady=5, sticky='w')
        self.cliente_entry = tk.Entry(form_frame, width=20)
        self.cliente_entry.grid(row=7, column=1, columnspan=2, padx=5, pady=5, sticky='w')

        # Fila 8: Pendiente y Guardar
        self.pendiente_var = tk.BooleanVar(value=False)  # desmarcado = completada
        tk.Checkbutton(form_frame, text="Dejar pendiente", variable=self.pendiente_var).grid(row=8, column=0, columnspan=2, pady=5, sticky='w')
        tk.Button(form_frame, text="Guardar operación", command=lambda: self.guardar_operacion(ventana)).grid(row=8, column=2, columnspan=2, pady=5)

        # ---- Tabla de órdenes de la caja ----
        ordenes_frame = tk.LabelFrame(ventana, text="Operaciones en esta caja (doble clic para editar)")
        ordenes_frame.pack(fill='both', expand=True, padx=10, pady=5)

        filtro_frame = tk.Frame(ordenes_frame)
        filtro_frame.pack(fill='x', padx=5, pady=5)
        ventana.solo_pendientes_var = tk.BooleanVar()   # <-- asociado a la ventana
        tk.Checkbutton(filtro_frame, text="Ver solo pendientes", variable=ventana.solo_pendientes_var,
                       command=lambda: self.actualizar_tabla_caja(ventana)).pack(side='left')

        # Guardar referencia al filtro para no destruirlo
        ventana.filtro_frame = filtro_frame

        filtro_frame = tk.Frame(ordenes_frame)
        filtro_frame.pack(fill='x', padx=5, pady=5)
        self.solo_pendientes_var = tk.BooleanVar()
        tk.Checkbutton(filtro_frame, text="Ver solo pendientes", variable=self.solo_pendientes_var,
                       command=lambda: self.actualizar_tabla_caja(ventana)).pack(side='left')

        self.actualizar_labels()
        self.actualizar_tabla_caja(ventana)


    def usar_cotizacion_sugerida(self):
        tipo = self.tipo_var.get()        # 'compra' o 'venta'
        moneda = self.moneda_ref_var.get()
        datos = get_ultimas_cotizaciones()
        # Buscar par moneda/ARS (ej: 'USD/ARS')
        par = f"{moneda}/ARS"
        if par in datos:
            info = datos[par]
            cot = info.get(tipo)  # 'compra' o 'venta'
            if cot is not None and cot != 0:
                self.cotizacion_entry.delete(0, tk.END)
                self.cotizacion_entry.insert(0, f"{cot:.2f}")
            else:
                messagebox.showwarning("Sin datos", f"No hay cotización de {tipo} para {par}")
        else:
            # Intentar al revés: ARS/moneda (no es común pero por si acaso)
            par = f"ARS/{moneda}"
            if par in datos:
                info = datos[par]
                cot = info.get(tipo)
                if cot is not None and cot != 0:
                    self.cotizacion_entry.delete(0, tk.END)
                    self.cotizacion_entry.insert(0, f"{cot:.2f}")
                else:
                    messagebox.showwarning("Sin datos", f"No hay cotización de {tipo} para {par}")
            else:
                messagebox.showwarning("Sin datos", "No se encontraron cotizaciones para este par")



    def actualizar_labels(self):
        tipo = self.tipo_var.get()
        moneda_ref = self.moneda_ref_var.get()
        if tipo == 'venta':
            self.lbl_recibido.config(text="Recibí (cliente da ARS):")
            self.moneda_recibida_var.set('ARS')
            self.lbl_deberia.config(text=f"Debería dar (cajero {moneda_ref}):")
            self.lbl_dio.config(text=f"Dio efectivamente (cajero {moneda_ref}):")
            self.moneda_entregada_var.set(moneda_ref)
        else:
            self.lbl_recibido.config(text=f"Recibí (cliente da {moneda_ref}):")
            self.moneda_recibida_var.set(moneda_ref)
            self.lbl_deberia.config(text="Debería dar (cajero ARS):")
            self.lbl_dio.config(text="Dio efectivamente (cajero ARS):")
            self.moneda_entregada_var.set('ARS')

    def calcular_deberia(self):
        try:
            cot = float(self.cotizacion_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresá una cotización válida")
            return

        tipo = self.tipo_var.get()
        monto_rec_str = self.monto_recibido_entry.get().strip()
        if not monto_rec_str:
            messagebox.showwarning("Atención", "Ingresá el monto que dio el cliente")
            return
        try:
            monto_rec = float(monto_rec_str)
        except ValueError:
            messagebox.showerror("Error", "Monto recibido inválido")
            return

        if tipo == 'venta':
            monto_deberia = monto_rec / cot
        else:
            monto_deberia = monto_rec * cot

        self.monto_deberia_var.set(f"{monto_deberia:.2f}")
        self.monto_rec_calc = monto_rec
        self.monto_ent_calc = monto_deberia
        self.lbl_diferencia.config(text="")

    def usar_calculado(self):
        if self.monto_deberia_var.get():
            self.monto_dio_entry.delete(0, tk.END)
            self.monto_dio_entry.insert(0, self.monto_deberia_var.get())
            self.actualizar_diferencia()

    def actualizar_diferencia(self):
        if self.monto_ent_calc is None:
            return
        dio_str = self.monto_dio_entry.get().strip()
        if not dio_str:
            self.lbl_diferencia.config(text="")
            return
        try:
            dio = float(dio_str)
            dif = dio - self.monto_ent_calc
            if abs(dif) > 0.001:
                self.lbl_diferencia.config(text=f"Diferencia: {dif:.2f} (faltante si es negativo)")
            else:
                self.lbl_diferencia.config(text="")
        except ValueError:
            pass

    def guardar_operacion(self, ventana):
        tipo = self.tipo_var.get()
        moneda_ref = self.moneda_ref_var.get()
        try:
            monto_rec = float(self.monto_recibido_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Completá el monto recibido")
            return
        if self.monto_ent_calc is None:
            messagebox.showerror("Error", "Primero presioná 'Calcular'")
            return
        dio_str = self.monto_dio_entry.get().strip()
        if not dio_str:
            messagebox.showerror("Error", "Ingresá cuánto diste efectivamente")
            return
        try:
            monto_dio = float(dio_str)
        except ValueError:
            messagebox.showerror("Error", "Monto entregado inválido")
            return
        cot_str = self.cotizacion_entry.get().strip()
        try:
            cot = float(cot_str) if cot_str else 0.0
        except ValueError:
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
                       cot, cliente, estado, ventana.caja_id, self.usuario_actual['id'])
        messagebox.showinfo("Éxito", "Operación registrada.")

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

        self.actualizar_tabla_caja(ventana)
        for widget in self.winfo_children():
            if isinstance(widget, tk.LabelFrame) and widget.cget('text') == 'Todas las órdenes':
                self.actualizar_vista_ordenes_general(widget)
                break

    # ---------- Tabla de caja (con deuda y doble clic) ----------
    def actualizar_tabla_caja(self, ventana):
        # Encontrar el ordenes_frame (igual que antes)
        for child in ventana.winfo_children():
            if isinstance(child, tk.LabelFrame) and 'Operaciones' in child.cget('text'):
                ordenes_frame = child
                break
        # Destruir todos los widgets excepto el filtro
        for w in ordenes_frame.winfo_children():
            if w != ventana.filtro_frame:
                w.destroy()

        # Leer el estado del filtro desde la ventana
        solo_pend = ventana.solo_pendientes_var.get()
        ordenes = get_ordenes_por_caja(caja_id=ventana.caja_id, limite=50, solo_pendientes=solo_pend)

        columnas = ['ID', 'Fecha', 'Tipo', 'Recibido', 'Entregado', 'Deuda', 'Estado', 'Cliente']
        tree = ttk.Treeview(ordenes_frame, columns=columnas, show='headings', height=10)
        tree.heading('ID', text='ID')
        tree.heading('Fecha', text='Fecha')
        tree.heading('Tipo', text='Tipo')
        tree.heading('Recibido', text='Recibido')
        tree.heading('Entregado', text='Entregado')
        tree.heading('Deuda', text='Deuda')
        tree.heading('Estado', text='Estado')
        tree.heading('Cliente', text='Cliente')
        tree.column('ID', width=40)
        tree.column('Fecha', width=120)
        tree.column('Tipo', width=60)
        tree.column('Recibido', width=140)
        tree.column('Entregado', width=140)
        tree.column('Deuda', width=80)
        tree.column('Estado', width=80)
        tree.column('Cliente', width=120)

        for o in ordenes:
            recibido = f"{o[3]} {o[5]:.2f}" if o[5] is not None else f"{o[3]} 0.00"
            entregado = f"{o[6]} {o[8]:.2f}" if o[8] is not None else f"{o[6]} 0.00"
            deuda = ""
            if o[11] == 'pendiente' and o[7] is not None and o[8] is not None:
                falta = o[7] - o[8]  # calculado - real
                if falta > 0.001:
                    deuda = f"{o[6]} {falta:.2f}"      # ej. "USD 6.50"
                elif falta < -0.001:
                    deuda = f"{o[6]} sobra {-falta:.2f}"
                elif falta < -0.001:
                    deuda = f"sobra {-falta:.2f}"
            tree.insert('', 'end', values=(o[0], o[1], o[2], recibido, entregado, deuda, o[11], o[10] or ""),
                        tags=(o[11],))
        tree.tag_configure('pendiente', background='#fff3cd')  # amarillo claro
        tree.tag_configure('completada', background='#d4edda')  # verde claro
        tree.pack(fill='both', expand=True)

        # Doble clic para editar
        tree.bind("<Double-1>", lambda event: self.editar_orden_desde_tabla(event, tree, ventana))

    def editar_orden_desde_tabla(self, event, tree, ventana):
        selected = tree.selection()
        if not selected:
            return
        item = tree.item(selected[0])
        id_orden = item['values'][0]  # ID está en la primera columna
        # Obtener orden completa de la base de datos
        ordenes = get_ordenes_por_caja(caja_id=ventana.caja_id, limite=1000)  # buscar la orden
        orden_data = None
        for o in ordenes:
            if o[0] == id_orden:
                orden_data = o
                break
        if orden_data:
            self.abrir_editor_orden(orden_data, ventana)

    def abrir_editor_orden(self, orden, ventana):
        id_orden = orden[0]
        moneda_rec = orden[3]
        moneda_ent = orden[6]
        rec_calc = orden[4]   # lo que el cliente debe dar (siempre igual al real)
        rec_real = orden[5]
        ent_calc = orden[7]   # lo que el cajero debía dar originalmente
        ent_real = orden[8]   # lo que el cajero lleva entregado realmente
        estado_actual = orden[11]

        editor = tk.Toplevel(self)
        editor.title(f"Orden {id_orden} – Gestionar entregas")
        editor.geometry("500x500")

        # Título destacado: tipo de operación (Compra / Venta)
        tipo_operacion = orden[2].capitalize()  # 'compra' -> 'Compra'
        tk.Label(editor, text=f"{tipo_operacion}", font=('Arial', 14, 'bold')).pack(pady=5)

        # Línea secundaria: caja, cotización, cliente, ID
        nombre_caja = orden[12]  # c.nombre (última columna de get_ordenes_por_caja)
        texto_secundario = f"Caja: {nombre_caja}  |  Cotización: {orden[9]:.2f}  |  Cliente: {orden[10] or '-'}  |  ID: #{id_orden}"
        tk.Label(editor, text=texto_secundario, font=('Arial', 10)).pack(pady=2)


        # Frame resumen
        resumen_frame = tk.LabelFrame(editor, text="Resumen de la operación")
        resumen_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(resumen_frame, text=f"Cliente dio:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        tk.Label(resumen_frame, text=f"{moneda_rec} {rec_real:.2f}").grid(row=0, column=1, padx=5, pady=2, sticky='w')

        tk.Label(resumen_frame, text=f"Cajero debe dar:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        tk.Label(resumen_frame, text=f"{moneda_ent} {ent_calc:.2f}").grid(row=1, column=1, padx=5, pady=2, sticky='w')

        tk.Label(resumen_frame, text=f"Entregado hasta ahora:").grid(row=2, column=0, padx=5, pady=2, sticky='w')
        tk.Label(resumen_frame, text=f"{moneda_ent} {ent_real:.2f}").grid(row=2, column=1, padx=5, pady=2, sticky='w')

        # Deuda
        deuda_actual = ent_calc - ent_real
        deuda_label = tk.Label(resumen_frame, text="Deuda pendiente:", fg="red")
        deuda_label.grid(row=3, column=0, padx=5, pady=2, sticky='w')
        deuda_valor_label = tk.Label(resumen_frame, text=f"{moneda_ent} {deuda_actual:.2f}" if deuda_actual > 0.001 else "Saldado", fg="red")
        deuda_valor_label.grid(row=3, column=1, padx=5, pady=2, sticky='w')

        # Frame nueva entrega
        entrega_frame = tk.LabelFrame(editor, text="Nueva entrega (agrega a lo ya entregado)")
        entrega_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(entrega_frame, text=f"Monto a entregar ahora ({moneda_ent}):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        nueva_entrega_entry = tk.Entry(entrega_frame, width=12)
        nueva_entrega_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(entrega_frame, text="(se sumará al real actual)").grid(row=0, column=2, padx=5, pady=5, sticky='w')

        def agregar_entrega():
            try:
                monto = float(nueva_entrega_entry.get())
                if monto <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Ingresá un monto positivo")
                return
            nuevo_real = ent_real + monto
            # Actualizar en BD y refrescar etiquetas
            actualizar_reales_orden(id_orden, rec_real, nuevo_real, None)  # estado lo decide el combo después
            # Refrescar ventana
            editor.destroy()
            # Reabrimos con datos frescos
            orden_actualizada = get_ordenes_por_caja(caja_id=ventana.caja_id, limite=1000)
            for o in orden_actualizada:
                if o[0] == id_orden:
                    self.abrir_editor_orden(o, ventana)
                    break
            # Refrescamos tablas
            self.actualizar_tabla_caja(ventana)
            for widget in self.winfo_children():
                if isinstance(widget, tk.LabelFrame) and widget.cget('text') == 'Todas las órdenes':
                    self.actualizar_vista_ordenes_general(widget)
                    break

        tk.Button(entrega_frame, text="Agregar entrega", command=agregar_entrega).grid(row=1, column=0, columnspan=2, pady=5)

        # Botón entregar total
        def entregar_total():
            actualizar_reales_orden(id_orden, rec_real, ent_calc, 'completada')
            messagebox.showinfo("Saldado", "Deuda saldada, orden completada.")
            editor.destroy()
            self.actualizar_tabla_caja(ventana)
            for widget in self.winfo_children():
                if isinstance(widget, tk.LabelFrame) and widget.cget('text') == 'Todas las órdenes':
                    self.actualizar_vista_ordenes_general(widget)
                    break

        tk.Button(editor, text="Entregar total (saldar deuda)", command=entregar_total).pack(pady=5)

        # Campos de edición directa de reales (por si hay que corregir)
        edit_frame = tk.LabelFrame(editor, text="Edición directa de reales (uso excepcional)")
        edit_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(edit_frame, text="Recibido real:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        entry_rec_real = tk.Entry(edit_frame, width=12)
        entry_rec_real.insert(0, f"{rec_real:.2f}")
        entry_rec_real.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(edit_frame, text="Entregado real:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        entry_ent_real = tk.Entry(edit_frame, width=12)
        entry_ent_real.insert(0, f"{ent_real:.2f}")
        entry_ent_real.grid(row=1, column=1, padx=5, pady=5)

        # Estado
        tk.Label(edit_frame, text="Estado:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        estado_var = tk.StringVar(value=estado_actual)
        ttk.Combobox(edit_frame, textvariable=estado_var, values=['pendiente', 'completada'], state='readonly').grid(row=2, column=1, padx=5, pady=5)

        def guardar_cambios_directos():
            try:
                nuevo_rec = float(entry_rec_real.get())
                nuevo_ent = float(entry_ent_real.get())
            except ValueError:
                messagebox.showerror("Error", "Valores numéricos inválidos")
                return
            actualizar_reales_orden(id_orden, nuevo_rec, nuevo_ent, estado_var.get())
            messagebox.showinfo("Guardado", "Cambios aplicados.")
            editor.destroy()
            self.actualizar_tabla_caja(ventana)
            for widget in self.winfo_children():
                if isinstance(widget, tk.LabelFrame) and widget.cget('text') == 'Todas las órdenes':
                    self.actualizar_vista_ordenes_general(widget)
                    break

        tk.Button(edit_frame, text="Guardar cambios", command=guardar_cambios_directos).grid(row=3, column=0, columnspan=2, pady=5)

        # Actualizar deuda visual al modificar reales directamente
        def actualizar_deuda_visual(*args):
            try:
                rec = float(entry_rec_real.get())
                ent = float(entry_ent_real.get())
            except:
                return
            deuda = ent_calc - ent
            deuda_valor_label.config(text=f"{moneda_ent} {deuda:.2f}" if abs(deuda) > 0.001 else "Saldado")
        entry_ent_real.bind('<KeyRelease>', actualizar_deuda_visual)
        entry_rec_real.bind('<KeyRelease>', actualizar_deuda_visual)

        tk.Button(editor, text="Cerrar", command=editor.destroy).pack(pady=5)


    def toggle_filtro_caja(self, caja_id):
        self.filtro_caja_id.set(caja_id)
        for btn in self.botones_caja_filtro:
            btn.configure(bg='#f0f0f0')
        # Activar el botón correspondiente
        if caja_id == 0:
            self.botones_caja_filtro[0].configure(bg='#4CAF50')
        else:
            for i, caja in enumerate(get_cajas()):
                if caja[0] == caja_id:
                    self.botones_caja_filtro[i+1].configure(bg='#4CAF50')
                    break
        self.actualizar_ordenes_filtradas()

    def toggle_filtro_tipo(self, tipo):
        self.filtro_tipo.set(tipo)
        for btn in self.botones_tipo_filtro:
            btn.configure(bg='#f0f0f0')
        if tipo == '':
            self.botones_tipo_filtro[0].configure(bg='#4CAF50')
        elif tipo == 'compra':
            self.botones_tipo_filtro[1].configure(bg='#4CAF50')
        elif tipo == 'venta':
            self.botones_tipo_filtro[2].configure(bg='#4CAF50')
        self.actualizar_ordenes_filtradas()

    def toggle_filtro_estado(self, estado):
        self.filtro_estado.set(estado)
        for btn in self.botones_estado_filtro:
            btn.configure(bg='#f0f0f0')
        if estado == '':
            self.botones_estado_filtro[0].configure(bg='#4CAF50')
        elif estado == 'pendiente':
            self.botones_estado_filtro[1].configure(bg='#4CAF50')
        elif estado == 'completada':
            self.botones_estado_filtro[2].configure(bg='#4CAF50')
        self.actualizar_ordenes_filtradas()

    def actualizar_ordenes_filtradas(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.LabelFrame) and widget.cget('text') == 'Todas las órdenes':
                self.actualizar_vista_ordenes_general(widget)
                break



    def abrir_form_cotizacion(self):
        ventana = tk.Toplevel(self)
        ventana.title("Nueva Cotización")
        ventana.geometry("350x300")

        tk.Label(ventana, text="Moneda base (de referencia):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        base_var = tk.StringVar(value='USD')
        base_combo = ttk.Combobox(ventana, textvariable=base_var, values=MONEDAS, state='readonly', width=6)
        base_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(ventana, text="Moneda de cotización:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        cot_var = tk.StringVar(value='ARS')
        cot_combo = ttk.Combobox(ventana, textvariable=cot_var, values=MONEDAS, state='readonly', width=6)
        cot_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        tk.Label(ventana, text=f"Compra (cuánto {cot_var.get()} por 1 {base_var.get()}):").grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        compra_entry = tk.Entry(ventana)
        compra_entry.grid(row=3, column=0, padx=5, pady=5)

        tk.Label(ventana, text=f"Venta (cuánto {cot_var.get()} por 1 {base_var.get()}):").grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        venta_entry = tk.Entry(ventana)
        venta_entry.grid(row=5, column=0, padx=5, pady=5)

        # Actualizar etiquetas al cambiar la moneda de cotización
        def actualizar_etiquetas(*args):
            base = base_var.get()
            cot = cot_var.get()
            tk.Label(ventana, text=f"Compra (cuánto {cot} por 1 {base}):").grid(row=2, column=0, columnspan=2)
            tk.Label(ventana, text=f"Venta (cuánto {cot} por 1 {base}):").grid(row=4, column=0, columnspan=2)

        cot_var.trace('w', actualizar_etiquetas)

        def guardar():
            base = base_var.get()
            cot = cot_var.get()
            if base == cot:
                messagebox.showerror("Error", "Las monedas no pueden ser iguales")
                return
            compra_str = compra_entry.get().strip()
            venta_str = venta_entry.get().strip()
            try:
                compra_val = float(compra_str) if compra_str else 0.0
                venta_val = float(venta_str) if venta_str else 0.0
            except ValueError:
                messagebox.showerror("Error", "Los precios deben ser números válidos")
                return
            if compra_val == 0 and venta_val == 0:
                messagebox.showwarning("Atención", "No se ingresó ningún precio. No se guardó la cotización.")
                return

            insertar_cotizacion(base, cot, compra_val, venta_val, self.usuario_actual['id'])

            # Escribir en los Excels (si corresponde) – Nota: el mapeo de celdas ahora deberá adaptarse si se usa
            """if compra_val != 0:
                actualizar_precio_en_todos(f"{base}/{cot}", 'compra', compra_val)
            if venta_val != 0:
                actualizar_precio_en_todos(f"{base}/{cot}", 'venta', venta_val)
            """
            messagebox.showinfo("Éxito", f"Cotización {base}/{cot} guardada.")
            ventana.destroy()
            self.mostrar_panel_admin()

        tk.Button(ventana, text="Guardar", command=guardar).grid(row=6, columnspan=2, pady=15)
        
    # ---------- Utilidades ----------
    def limpiar_ventana(self):
        for widget in self.winfo_children():
            widget.destroy()

    def cerrar_sesion(self):
        self.usuario_actual = None
        self.mostrar_login()

if __name__ == '__main__':
    init_db()
    app = App()
    app.mainloop()