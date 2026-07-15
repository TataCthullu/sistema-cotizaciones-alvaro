import tkinter as tk
from formato_argentino import formato_argentino

class EntryNumerico(tk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        vcmd = (self.register(self._validar), '%P')
        self.config(validate='key', validatecommand=vcmd)
        self.bind('<FocusOut>', self._formatear)

    def _validar(self, texto):
        if texto == "":
            return True
        for c in texto:
            if not (c.isdigit() or c in (',', '.')):
                return False
        return True

    def _formatear(self, event=None):
        raw = self.get().strip()
        if not raw:
            return
        temp = raw.replace('.', '').replace(',', '.')
        try:
            value = float(temp)
        except ValueError:
            return
        self.delete(0, tk.END)
        self.insert(0, formato_argentino(value))

    def get_value(self):
        texto = self.get().strip()
        if not texto:
            return 0.0
        texto = texto.replace('.', '').replace(',', '.')
        try:
            return float(texto)
        except ValueError:
            return 0.0

    def set_value(self, value, decimales=2):
        self.delete(0, tk.END)
        self.insert(0, formato_argentino(value, decimales))

    @staticmethod
    def get_value_from_text(texto):
        """Devuelve float interpretando comas y puntos."""
        if not texto.strip():
            return 0.0
        texto = texto.replace('.', '').replace(',', '.')
        try:
            return float(texto)
        except ValueError:
            raise ValueError("Valor inválido")    