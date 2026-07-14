import tkinter as tk
from tkinter import ttk, messagebox
from database import (
    init_db, validar_login, insertar_cotizacion, get_ultimas_cotizaciones,
    get_ordenes_por_caja, get_cajas, get_historial_cotizaciones
)
from numerical_entry import EntryNumerico
from config import MONEDAS

MONEDAS_EXT = [m for m in MONEDAS if m != "ARS"]

class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panel Admin")
        self.geometry("1000x750")
        self.usuario_actual = None
        # Filtros del admin
        self.filtro_caja_id = tk.IntVar(value=0)  # 0 = todas
        self.filtro_tipo = tk.StringVar(value='')
        self.filtro_estado = tk.StringVar(value='')
        
        self.filtro_cliente_var = tk.StringVar(value='')
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
        if user and user['rol'] == 'admin':
            self.usuario_actual = user
            self.mostrar_panel_admin()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    # ---------- Panel Admin ----------
    def mostrar_panel_admin(self):
        self.limpiar_ventana()
        self.geometry("1000x750")
        tk.Label(self, text="Panel Administrador",
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


        # Filtro por cliente
        tk.Label(filtros_frame, text="Cliente:").pack(side='left', padx=5)
        entry_cliente = tk.Entry(filtros_frame, textvariable=self.filtro_cliente_var, width=15)
        self.filtro_cliente_var.trace('w', lambda *args: self.actualizar_ordenes_filtradas())
        entry_cliente.pack(side='left', padx=2)


        # Tabla de órdenes
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

    # ---------- Tabla general de órdenes ----------
    def actualizar_vista_ordenes_general(self, frame):
        for w in frame.winfo_children():
            w.destroy()
        caja_id = self.filtro_caja_id.get() if self.filtro_caja_id.get() != 0 else None
        tipo_op = self.filtro_tipo.get() if self.filtro_tipo.get() else None
        estado = self.filtro_estado.get() if self.filtro_estado.get() else None
        ordenes = get_ordenes_por_caja(caja_id=caja_id, limite=50, tipo_operacion=tipo_op, estado=estado)
        
        # Filtrar por cliente si hay texto
        texto_cliente = self.filtro_cliente_var.get().strip().lower()
        if texto_cliente:
            ordenes = [o for o in ordenes if o[10] and texto_cliente in o[10].lower()]
        
        columnas = ['ID', 'Fecha', 'Tipo', 'Recibido', 'Entregado', 'Cotización', 'Deuda', 'Estado', 'Cliente']
        tree = ttk.Treeview(frame, columns=columnas, show='headings', height=10)
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
        tree.column('Deuda', width=100)
        tree.column('Estado', width=80)
        tree.column('Cliente', width=120)

        for o in ordenes:
            recibido = f"{o[3]} {o[5]:.2f}" if o[5] is not None else f"{o[3]} 0.00"
            entregado = f"{o[6]} {o[8]:.2f}" if o[8] is not None else f"{o[6]} 0.00"
            deuda = ""
            if o[11] == 'pendiente' and o[7] is not None and o[8] is not None:
                falta = o[7] - o[8]
                if falta > 0.001:
                    deuda = f"{o[6]} {falta:.2f}"
            tree.insert('', 'end', values=(o[0], o[1], o[2], recibido, entregado, f"{o[9]:.2f}" if o[9] else "—", deuda, o[11], o[10] or ""), tags=(o[11],))

        tree.tag_configure('pendiente', background='#fff3cd')
        tree.tag_configure('completada', background='#d4edda')
        tree.pack(fill='both', expand=True)

    # ---------- Filtros ----------
    def toggle_filtro_caja(self, caja_id):
        self.filtro_caja_id.set(caja_id)
        for btn in self.botones_caja_filtro:
            btn.configure(bg='#f0f0f0')
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

    # ---------- Nueva Cotización ----------
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
    app = AdminApp()
    app.mainloop()