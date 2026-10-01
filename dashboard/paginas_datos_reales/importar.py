"""Pestaña «Importar»: subir un reporte, ver el formato reconocido y el resultado de la validación,
y recién confirmar para que se guarde. Siempre importa a la base propia, sin importar qué fuente esté
elegida en las demás pestañas."""
import importlib.util
from pathlib import Path

import streamlit as st

# Leer PDF y migrar la base necesitan requirements-datos.txt, que el deploy público (Streamlit Cloud) no
# instala a propósito: los reportes reales se importan solo en la copia local del tablero. Sin estas
# dependencias, la pestaña lo explica en vez de ofrecer subir un archivo que después rompería la página.
_DEPENDENCIAS = ("pdfplumber", "alembic")

_CLAVE_NOMBRE = "_importar_nombre_seguro"
_CLAVE_PREVIA = "_importar_previa"
_CLAVE_ARCHIVO_ID = "_importar_archivo_id"
_CLAVE_GENERACION = "_importar_generacion"
_CLAVE_ULTIMO_RESULTADO = "_importar_ultimo_resultado"


def _limpiar(nueva_generacion: bool = False) -> None:
    st.session_state.pop(_CLAVE_NOMBRE, None)
    st.session_state.pop(_CLAVE_PREVIA, None)
    st.session_state.pop(_CLAVE_ARCHIVO_ID, None)
    if nueva_generacion:
        st.session_state[_CLAVE_GENERACION] = st.session_state.get(_CLAVE_GENERACION, 0) + 1


def _mostrar_chequeos(validacion) -> None:
    for chequeo in validacion.chequeos:
        (st.success if chequeo.ok else st.error)(f"{chequeo.nombre}: {chequeo.detalle}")


def _faltan_dependencias() -> list[str]:
    return [modulo for modulo in _DEPENDENCIAS if importlib.util.find_spec(modulo) is None]


def render() -> None:
    st.subheader("Importar un reporte")
    if _faltan_dependencias():
        st.info("ℹ️ La importación de reportes funciona solo en la copia local del tablero, para que los "
                "datos reales no pasen por la versión publicada.")
        st.caption("Para usarla en tu computadora: instalá `requirements-datos.txt` y configurá "
                   "`ANON_SECRET` en el archivo `.env`.")
        return

    st.caption(
        "Subí un PDF de VISOC. Primero vas a ver qué formato se reconoció y si valida contra sus "
        "propios totales — recién si tocás «Confirmar e importar» se guarda en la base."
    )

    if _CLAVE_ULTIMO_RESULTADO in st.session_state:
        resultado = st.session_state.pop(_CLAVE_ULTIMO_RESULTADO)
        if resultado.estado in ("ok", "con_advertencias"):
            st.success(f"✅ El reporte se guardó ({resultado.filas_leidas} filas).")
            for advertencia in resultado.advertencias:
                st.warning(f"⚠️ {advertencia}")
        else:
            st.error("❌ El reporte quedó rechazado: no se guardó en el modelo. Queda registrado "
                     "para revisar más tarde.")
            for advertencia in resultado.advertencias:
                st.caption(advertencia)

    generacion = st.session_state.get(_CLAVE_GENERACION, 0)
    archivo = st.file_uploader("Reporte (PDF)", type=["pdf"], key=f"_importar_archivo_{generacion}")

    if archivo is None:
        _limpiar()
        return

    if st.session_state.get(_CLAVE_ARCHIVO_ID) != archivo.file_id:
        _limpiar()
        import tempfile

        from sqlalchemy.orm import Session

        from datos.anonimizador import Anonimizador
        from datos.config import ConfiguracionFaltante, anon_secret
        from datos.importar import nombre_archivo_seguro, previsualizar
        from datos.sesion import crear_engine, migrar

        try:
            anonimizador = Anonimizador(anon_secret())
        except ConfiguracionFaltante as error:
            st.warning(f"⚠️ {error}")
            return

        nombre_seguro = nombre_archivo_seguro(archivo.name)
        migrar()
        # El archivo real (con datos personales todavía sin anonimizar hasta que `previsualizar` los
        # procese) solo existe en disco durante este bloque — se borra apenas se termina de leer, en
        # vez de sostenerlo en session_state hasta que se confirme o se descarte (encontrado en la
        # revisión final: la versión anterior podía dejar una copia huérfana en el temporal del
        # sistema si algo fallaba entre la lectura y la confirmación). `confirmar()` más abajo solo
        # necesita el nombre (`.name`/`.suffix`), nunca vuelve a leer el archivo.
        with tempfile.TemporaryDirectory(prefix="vivso_importar_") as carpeta:
            ruta = Path(carpeta) / nombre_seguro
            ruta.write_bytes(archivo.getvalue())
            with Session(crear_engine()) as sesion:
                previa = previsualizar(ruta, sesion, anonimizador)

        st.session_state[_CLAVE_NOMBRE] = nombre_seguro
        st.session_state[_CLAVE_PREVIA] = previa
        st.session_state[_CLAVE_ARCHIVO_ID] = archivo.file_id

    previa = st.session_state.get(_CLAVE_PREVIA)
    if previa is None:        # se cortó arriba por falta de ANON_SECRET
        return

    if previa.importador is None:
        st.warning("⚠️ No se reconoce este formato de archivo. No hay nada para importar.")
        if st.button("Descartar", key="descartar_no_reconocido"):
            _limpiar(nueva_generacion=True)
            st.rerun()
        return

    st.success(f"✅ Formato reconocido: **{previa.importador.codigo}**")

    if previa.lectura is None:
        st.error(f"❌ No se pudo leer el archivo ({previa.error_lectura}). "
                 "¿Es el PDF tal como lo exporta VISOC, sin modificar?")
        if st.button("Descartar", key="descartar_ilegible"):
            _limpiar(nueva_generacion=True)
            st.rerun()
        return

    st.metric("Filas leídas", len(previa.lectura.filas))
    _mostrar_chequeos(previa.validacion)
    for advertencia in previa.lectura.advertencias:
        st.warning(f"⚠️ {advertencia}")

    forzar = False
    if previa.duplicada is not None:
        st.info(
            f"ℹ️ Este archivo ya se importó el {previa.duplicada.importado_en:%d/%m/%Y} "
            f"(estado: {previa.duplicada.estado}).")
        forzar = st.checkbox("Importar de nuevo igual")

    if not previa.validacion.ok:
        st.warning(
            "⚠️ Este reporte no coincide con sus propios totales. Si confirmás, queda registrado "
            "como rechazado — sirve para no perder el archivo, no se carga al tablero."
        )

    puede_confirmar = previa.duplicada is None or forzar
    etiqueta_confirmar = "Confirmar e importar" if previa.validacion.ok else "Registrar como rechazado"
    c1, c2 = st.columns(2)
    if c1.button(etiqueta_confirmar, disabled=not puede_confirmar, type="primary"):
        from sqlalchemy.orm import Session

        from datos.importar import confirmar
        from datos.sesion import crear_engine, sembrar_catalogos

        with Session(crear_engine()) as sesion:
            # Mismo camino que la CLI (`datos/importar.py::main`) y la API (`datos/api/importar.py`):
            # sin sembrar catálogos, un Organizacion/Vivienda con FK a un catálogo (ej. Clasificacion)
            # queda con esos campos en None (encontrado en la revisión final — el mismo bug que ya se
            # había corregido en la API del Plan 4, pero el tablero no lo heredó).
            sembrar_catalogos(sesion)
            resultado = confirmar(previa, Path(st.session_state[_CLAVE_NOMBRE]), sesion, forzar=forzar)
        _limpiar(nueva_generacion=True)
        st.session_state[_CLAVE_ULTIMO_RESULTADO] = resultado
        st.rerun()
    if c2.button("Descartar", key="descartar_confirmable"):
        _limpiar(nueva_generacion=True)
        st.rerun()
