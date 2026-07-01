import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import openpyxl
from datetime import datetime
import os

# ===================== CONFIGURACIÓN =====================
# config.py

# Base de datos
DATABASE = "cambios.db"

# Lista de archivos Excel que deben actualizarse con el precio del admin.
# Poné todas las rutas (pueden ser relativas a la carpeta del script o absolutas).
# Ejemplo: el admin usa "exl_main.xlsx", el cajero1 "caja1.xlsx", cajero2 "caja2.xlsx", etc.
EXCEL_FILES = [
    "exl_main.xlsx",   # Admin/General
    #"caja1.xlsx",      # Cajero 1 (Álvaro como cajero, o quien sea)
    #"caja2.xlsx",      # Cajero 2 (Roberto)
    # Podés agregar "caja3.xlsx", "caja4.xlsx", etc.
]

# Mapeo de (moneda, tipo) a celda en el Excel
MAPEO_CELDAS = {
    ("USD", "compra"): "C51",
    ("USD", "venta"):  "C52",
    ("EUR", "compra"): "E51",
    ("EUR", "venta"):  "E52",
    ("USDT", "compra"): "U13",
    ("USDT", "venta"):  "X13",
    # Agregá más monedas si usan, ej. ("ORO", "compra"): "AA51"
}

# Credenciales por defecto del admin (se crean la primera vez)
DEFAULT_ADMIN = "admin"
DEFAULT_ADMIN_PASS = "admin123"

# Lista de monedas que aparecen en la interfaz
MONEDAS = ["ARS", "USD", "EUR", "USDT"]   # podés agregar "ORO", etc.

# ===================== BASE DE DATOS =====================
def init_db():
    conn = sqlite3.connect('cambios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        nombre TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('admin','cajero')) NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cotizaciones (
        id INTEGER PRIMARY KEY,
        moneda TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('compra','venta')) NOT NULL,
        precio REAL NOT NULL,
        fecha_hora TEXT DEFAULT (datetime('now')),
        usuario_id INTEGER,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    # Crear admin por defecto (admin / admin123)
    try:
        c.execute("INSERT INTO usuarios (nombre, password_hash, rol) VALUES (?,?,?)",
                  ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin'))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

def get_ultimas_cotizaciones():
    conn = sqlite3.connect('cambios.db')
    c = conn.cursor()
    c.execute('''SELECT moneda, tipo, precio, fecha_hora FROM cotizaciones
                 WHERE id IN (SELECT MAX(id) FROM cotizaciones GROUP BY moneda, tipo)''')
    datos = {}
    for moneda, tipo, precio, fecha in c.fetchall():
        if moneda not in datos:
            datos[moneda] = {}
        datos[moneda][tipo] = (precio, fecha)
    conn.close()
    return datos

def insertar_cotizacion(moneda, tipo, precio, usuario_id):
    conn = sqlite3.connect('cambios.db')
    c = conn.cursor()
    c.execute("INSERT INTO cotizaciones (moneda, tipo, precio, usuario_id) VALUES (?,?,?,?)",
              (moneda, tipo, precio, usuario_id))
    conn.commit()
    conn.close()

def validar_login(nombre, password):
    conn = sqlite3.connect('cambios.db')
    c = conn.cursor()
    c.execute("SELECT id, rol, password_hash FROM usuarios WHERE nombre=?", (nombre,))
    user = c.fetchone()
    conn.close()
    if user and user[2] == hashlib.sha256(password.encode()).hexdigest():
        return {'id': user[0], 'rol': user[1]}
    return None

# ===================== FUNCIÓN PARA ESCRIBIR EN EXCEL =====================
def escribir_en_excel(moneda, tipo, precio):
    """
    Abre el archivo Excel indicado en RUTA_EXCEL, escribe el precio en la celda
    correspondiente según MAPEO_CELDAS y guarda los cambios.
    """
    celda = MAPEO_CELDAS.get((moneda, tipo))
    if not celda:
        print(f"No hay mapeo definido para {moneda} {tipo}. El precio NO se escribió en Excel.")
        return False

    try:
        # Verificar que el archivo existe
        if not os.path.exists(EXCEL_FILES):
            messagebox.showerror("Error", f"No se encontró el archivo Excel:\n{EXCEL_FILES}")
            return False

        wb = openpyxl.load_workbook(EXCEL_FILES)
        ws = wb.active   # Asume que la hoja activa es la correcta
        ws[celda] = precio
        wb.save(EXCEL_FILES)
        return True
    except PermissionError:
        messagebox.showerror("Error", "No se puede escribir en el Excel.\nCiérralo antes de guardar cotizaciones.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo escribir en el Excel:\n{e}")
        return False

# ===================== INTERFAZ GRÁFICA =====================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Cotizaciones - Álvaro")
        self.geometry("600x400")
        self.usuario_actual = None
        self.mostrar_login()

    # ---------- Pantalla de login ----------
    def mostrar_login(self):
        for widget in self.winfo_children():
            widget.destroy()
        tk.Label(self, text="Usuario:").pack()
        self.entry_user = tk.Entry(self)
        self.entry_user.pack()
        tk.Label(self, text="Contraseña:").pack()
        self.entry_pass = tk.Entry(self, show="*")
        self.entry_pass.pack()
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
        for widget in self.winfo_children():
            widget.destroy()
        self.geometry("650x450")
        tk.Label(self, text=f"Panel Administrador - Usuario: {self.usuario_actual['id']}", font=('Arial', 14)).pack(pady=10)

        frame_cot = tk.LabelFrame(self, text="Cotizaciones actuales")
        frame_cot.pack(fill='both', expand=True, padx=10, pady=10)
        self.actualizar_vista_cotizaciones(frame_cot)

        tk.Button(self, text="Nueva Cotización", command=self.abrir_form_cotizacion).pack(pady=10)
        tk.Button(self, text="Cerrar sesión", command=self.cerrar_sesion).pack(pady=5)

    # ---------- Panel Cajero ----------
    def mostrar_panel_cajero(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.geometry("650x450")
        tk.Label(self, text=f"Panel Cajero - Usuario: {self.usuario_actual['id']}", font=('Arial', 14)).pack(pady=10)

        frame_cot = tk.LabelFrame(self, text="Cotizaciones actuales")
        frame_cot.pack(fill='both', expand=True, padx=10, pady=10)
        self.actualizar_vista_cotizaciones(frame_cot)

        tk.Button(self, text="Cerrar sesión", command=self.cerrar_sesion).pack(pady=10)

    # ---------- Tabla de cotizaciones ----------
    def actualizar_vista_cotizaciones(self, frame):
        for w in frame.winfo_children():
            w.destroy()
        datos = get_ultimas_cotizaciones()
        columnas = ['Moneda', 'Compra', 'Venta']
        tree = ttk.Treeview(frame, columns=columnas, show='headings')
        for col in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        for moneda, tipos in datos.items():
            compra = f"${tipos['compra'][0]:.2f}" if 'compra' in tipos else "N/A"
            venta = f"${tipos['venta'][0]:.2f}" if 'venta' in tipos else "N/A"
            tree.insert('', 'end', values=(moneda, compra, venta))
        tree.pack(fill='both', expand=True)

    # ---------- Ventana para nueva cotización ----------
    def abrir_form_cotizacion(self):
        ventana = tk.Toplevel(self)
        ventana.title("Nueva Cotización")
        tk.Label(ventana, text="Moneda:").grid(row=0, column=0)
        moneda = ttk.Combobox(ventana, values=['USD', 'EUR', 'USDT'])
        moneda.grid(row=0, column=1)
        tk.Label(ventana, text="Tipo:").grid(row=1, column=0)
        tipo = ttk.Combobox(ventana, values=['compra', 'venta'])
        tipo.grid(row=1, column=1)
        tk.Label(ventana, text="Precio:").grid(row=2, column=0)
        precio = tk.Entry(ventana)
        precio.grid(row=2, column=1)

        def guardar():
            m = moneda.get()
            t = tipo.get()
            try:
                p = float(precio.get())
            except ValueError:
                messagebox.showerror("Error", "El precio debe ser un número válido")
                return
            if not m or not t:
                messagebox.showerror("Error", "Seleccioná moneda y tipo")
                return

            # 1. Guardar en base de datos (historial)
            insertar_cotizacion(m, t, p, self.usuario_actual['id'])

            # 2. Escribir en el Excel para que recalcule
            if escribir_en_excel(m, t, p):
                messagebox.showinfo("Éxito", f"Cotización {m} {t} guardada en BD y Excel.")
            else:
                messagebox.showwarning("Atención", "Cotización guardada en BD pero NO se pudo actualizar el Excel.")

            ventana.destroy()
            self.mostrar_panel_admin()

        tk.Button(ventana, text="Guardar", command=guardar).grid(row=3, columnspan=2, pady=10)

    # ---------- Cerrar sesión ----------
    def cerrar_sesion(self):
        self.usuario_actual = None
        self.mostrar_login()

# ===================== ARRANQUE =====================
if __name__ == '__main__':
    init_db()
    app = App()
    app.mainloop()