import sqlite3
import hashlib
from config import DATABASE, DEFAULT_ADMIN, DEFAULT_ADMIN_PASS

def conectar():
    return sqlite3.connect(DATABASE)

def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT CHECK(rol IN ('admin','cajero')) NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY,
            moneda TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('compra','venta')) NOT NULL,
            precio REAL NOT NULL,
            fecha_hora TEXT DEFAULT (datetime('now','localtime')),
            usuario_id INTEGER,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS cajas (
            id INTEGER PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY,
            fecha_hora TEXT DEFAULT (datetime('now','localtime')),
            tipo_operacion TEXT CHECK(tipo_operacion IN ('compra','venta')) NOT NULL,
            moneda_recibida TEXT NOT NULL,
            monto_recibido_calc REAL NOT NULL,
            monto_recibido_real REAL NOT NULL,
            moneda_entregada TEXT NOT NULL,
            monto_entregado_calc REAL NOT NULL,
            monto_entregado_real REAL NOT NULL,
            cotizacion REAL,
            cliente TEXT,
            estado TEXT DEFAULT 'completada' CHECK(estado IN ('pendiente','completada')),
            caja_id INTEGER,
            usuario_id INTEGER,
            FOREIGN KEY(caja_id) REFERENCES cajas(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # Admin por defecto
    try:
        c.execute("INSERT INTO usuarios (nombre, password_hash, rol) VALUES (?,?,?)",
                  (DEFAULT_ADMIN, hashlib.sha256(DEFAULT_ADMIN_PASS.encode()).hexdigest(), 'admin'))
    except sqlite3.IntegrityError:
        pass

    # Cajas iniciales
    for nombre in ["Caja 1", "Caja 2"]:
        try:
            c.execute("INSERT INTO cajas (nombre) VALUES (?)", (nombre,))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

def validar_login(nombre, password):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id, rol, password_hash FROM usuarios WHERE nombre=?", (nombre,))
    user = c.fetchone()
    conn.close()
    if user and user[2] == hashlib.sha256(password.encode()).hexdigest():
        return {'id': user[0], 'rol': user[1]}
    return None

def insertar_cotizacion(moneda, tipo, precio, usuario_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO cotizaciones (moneda, tipo, precio, usuario_id) VALUES (?,?,?,?)",
              (moneda, tipo, precio, usuario_id))
    conn.commit()
    conn.close()

def get_ultimas_cotizaciones():
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        SELECT moneda, tipo, precio, fecha_hora FROM cotizaciones
        WHERE id IN (SELECT MAX(id) FROM cotizaciones GROUP BY moneda, tipo)
    ''')
    datos = {}
    for moneda, tipo, precio, fecha in c.fetchall():
        if moneda not in datos:
            datos[moneda] = {}
        datos[moneda][tipo] = (precio, fecha)
    conn.close()
    return datos

def get_cajas():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id, nombre FROM cajas ORDER BY id")
    cajas = c.fetchall()
    conn.close()
    return cajas

def insertar_orden(tipo_operacion, moneda_recibida, monto_recibido_calc, monto_recibido_real,
                   moneda_entregada, monto_entregado_calc, monto_entregado_real,
                   cotizacion, cliente, estado, caja_id, usuario_id):
    conn = conectar()
    c = conn.cursor()
    c.execute('''INSERT INTO ordenes (tipo_operacion, moneda_recibida, monto_recibido_calc, monto_recibido_real,
                                      moneda_entregada, monto_entregado_calc, monto_entregado_real,
                                      cotizacion, cliente, estado, caja_id, usuario_id)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
              (tipo_operacion, moneda_recibida, monto_recibido_calc, monto_recibido_real,
               moneda_entregada, monto_entregado_calc, monto_entregado_real,
               cotizacion, cliente, estado, caja_id, usuario_id))
    conn.commit()
    conn.close()

def get_ordenes_por_caja(caja_id=None, limite=50, solo_pendientes=False):
    conn = conectar()
    c = conn.cursor()
    query = '''SELECT o.id, o.fecha_hora, o.tipo_operacion,
                      o.moneda_recibida, o.monto_recibido_calc, o.monto_recibido_real,
                      o.moneda_entregada, o.monto_entregado_calc, o.monto_entregado_real,
                      o.cotizacion, o.cliente, o.estado, c.nombre
               FROM ordenes o JOIN cajas c ON o.caja_id = c.id
               WHERE 1=1'''
    params = []
    if caja_id:
        query += " AND o.caja_id = ?"
        params.append(caja_id)
    if solo_pendientes:
        query += " AND o.estado = 'pendiente'"
    query += " ORDER BY o.id DESC LIMIT ?"
    params.append(limite)

    c.execute(query, params)
    ordenes = c.fetchall()
    conn.close()
    return ordenes

def marcar_orden_completada(id_orden):
    conn = conectar()
    c = conn.cursor()
    c.execute("UPDATE ordenes SET estado = 'completada' WHERE id = ?", (id_orden,))
    conn.commit()
    conn.close()

def actualizar_reales_orden(id_orden, nuevo_rec_real, nuevo_ent_real, estado=None):
    conn = conectar()
    c = conn.cursor()
    c.execute("UPDATE ordenes SET monto_recibido_real = ?, monto_entregado_real = ? WHERE id = ?",
              (nuevo_rec_real, nuevo_ent_real, id_orden))
    if estado is not None:
        c.execute("UPDATE ordenes SET estado = ? WHERE id = ?", (estado, id_orden))
    conn.commit()
    conn.close()