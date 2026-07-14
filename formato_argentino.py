def formato_argentino(valor, decimales=2):
    """
    Devuelve string formateado en estilo argentino.
    valor: float o None
    decimales: cantidad máxima de decimales a mostrar (sin ceros finales)
    """
    if valor is None:
        return "—"
    try:
        f = float(valor)
    except (ValueError, TypeError):
        return str(valor)

    # Redondear a la cantidad de decimales pedida
    formato = f"{{:.{decimales}f}}"
    redondeado = formato.format(f)
    entero, decimal = redondeado.split('.')

    # Formatear parte entera con puntos de miles
    try:
        int_entero = int(entero)
    except ValueError:
        int_entero = 0
    entero_formateado = "{:,}".format(int_entero).replace(',', '.')

    # Eliminar ceros a la derecha en la parte decimal
    decimal = decimal.rstrip('0')
    if decimal == '':
        return entero_formateado
    else:
        return f"{entero_formateado},{decimal}"