# excel_handler.py
import os
import openpyxl
from tkinter import messagebox
from config import EXCEL_FILES, MAPEO_CELDAS

def actualizar_precio_en_todos(moneda, tipo, precio):
    celda = MAPEO_CELDAS.get((moneda, tipo))
    if not celda:
        messagebox.showwarning("Mapeo faltante",
                               f"No hay celda definida para {moneda} {tipo}.")
        return False

    errores = []
    exitos = 0
    for ruta in EXCEL_FILES:
        if not os.path.exists(ruta):
            errores.append(f"No se encontró {ruta} (se omite)")
            continue
        try:
            wb = openpyxl.load_workbook(ruta)
            ws = wb.active
            ws[celda] = precio
            wb.save(ruta)
            exitos += 1
        except PermissionError:
            errores.append(f"{ruta} está abierto, ciérralo antes de actualizar.")
        except Exception as e:
            errores.append(f"Error en {ruta}: {e}")

    if not exitos and errores:
        messagebox.showerror("Error al actualizar Excel",
                             "No se pudo actualizar ningún archivo:\n" + "\n".join(errores))
        return False
    elif errores:
        messagebox.showwarning("Algunos archivos no se actualizaron",
                               "\n".join(errores))
    return True