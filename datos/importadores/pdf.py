"""Lectura fina de PDF: texto o tokens con su posición horizontal. Sin reglas de negocio."""
from pathlib import Path

import pdfplumber


def leer_lineas_texto(ruta: Path, max_paginas: int | None = None) -> list[str]:
    """Las líneas de texto del PDF, en orden."""
    salida: list[str] = []
    with pdfplumber.open(ruta) as pdf:
        for i, pagina in enumerate(pdf.pages):
            if max_paginas is not None and i >= max_paginas:
                break
            salida.extend((pagina.extract_text() or "").split("\n"))
    return salida


def leer_lineas_tokens(ruta: Path, max_paginas: int | None = None) -> list[list[tuple[str, float]]]:
    """Las líneas del PDF como listas de (texto, x0), en orden de lectura.
    La posición horizontal permite distinguir columnas vacías (por ejemplo, reclamo o acta)."""
    salida: list[list[tuple[str, float]]] = []
    with pdfplumber.open(ruta) as pdf:
        for i, pagina in enumerate(pdf.pages):
            if max_paginas is not None and i >= max_paginas:
                break
            por_linea: dict[int, list] = {}
            for palabra in pagina.extract_words():
                por_linea.setdefault(round(palabra["top"] / 3), []).append(palabra)
            for clave in sorted(por_linea):
                ordenadas = sorted(por_linea[clave], key=lambda p: p["x0"])
                salida.append([(p["text"], p["x0"]) for p in ordenadas])
    return salida
