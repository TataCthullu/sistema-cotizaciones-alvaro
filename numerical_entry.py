import tkinter as tk

class EntryNumerico(tk.Entry):
    """Entry que acepta comas y puntos, y devuelve float."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        vcmd = (self.register(self._validar), '%P')
        self.config(validate='key', validatecommand=vcmd)

    def _validar(self, texto):
        if texto == "":
            return True
        for c in texto:
            if not (c.isdigit() or c in (',', '.')):
                return False
        return True

    def get_value(self):
        """Devuelve el valor como float, interpretando comas como decimales."""
        texto = self.get().strip()
        if not texto:
            return 0.0
        # Quitar puntos de miles y cambiar coma decimal por punto
        texto = texto.replace('.', '').replace(',', '.')
        try:
            return float(texto)
        except ValueError:
            return 0.0

    def set_value(self, value):
        """Coloca un número, mostrándolo con punto decimal."""
        self.delete(0, tk.END)
        self.insert(0, str(value))