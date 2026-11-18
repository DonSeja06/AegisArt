from datetime import datetime

MESES_LARGO_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

MESES_CORTO_ES = {
    1: "ene",
    2: "feb",
    3: "mar",
    4: "abr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dic",
}


def formatear_fecha_es(fecha: datetime | None, estilo: str = "largo") -> str:
    """
    Formatea fechas en español de manera determinista sin depender del locale del sistema operativo.
    Estilos: 'largo' ('18 junio 2026'), 'corto_coma' ('18 jun, 2026'), 'dia_mes' ('18 jun').
    """
    if fecha is None:
        fecha = datetime.utcnow()
    if estilo == "corto_coma":
        return f"{fecha.day:02d} {MESES_CORTO_ES[fecha.month]}, {fecha.year}"
    if estilo == "dia_mes":
        return f"{fecha.day:02d} {MESES_CORTO_ES[fecha.month]}"
    return f"{fecha.day:02d} {MESES_LARGO_ES[fecha.month]} {fecha.year}"
