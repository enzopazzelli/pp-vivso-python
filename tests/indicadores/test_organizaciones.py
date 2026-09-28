from datetime import date, datetime

from datos.fuentes.propia import FuentePropia
from datos.importadores.visoc_por_solicitante import VisocPorSolicitante
from datos.indicadores.organizaciones import tasa_activacion_finalizacion
from datos.modelo import Importacion
from tests.fixtures_visoc import LINEAS_PS


def _importacion(sesion, huella="0" * 64, fecha_reporte=date(2026, 9, 2)):
    # `fecha_reporte` va acá porque en producción lo pone `importar_archivo` (Plan 1) al leer la línea
    # «Fecha:» del reporte; estas pruebas arman la importación a mano, sin pasar por ese camino.
    imp = Importacion(tipo_reporte="visoc_por_solicitante", archivo_nombre="x", archivo_huella=huella,
                      estado="leida", fecha_reporte=fecha_reporte, importado_en=datetime.now())
    sesion.add(imp)
    sesion.flush()
    return imp


def test_sin_datos_queda_no_disponible(sesion):
    indicador = tasa_activacion_finalizacion(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "no_disponible"


def test_con_una_sola_consulta_importada_queda_parcial(sesion):
    # Solo se importó "solicitadas": ninguna organización tiene datos de "activadas"
    importador = VisocPorSolicitante()
    importador.mapear(importador.lectura_desde_lineas(LINEAS_PS), sesion, _importacion(sesion))
    sesion.commit()

    indicador = tasa_activacion_finalizacion(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "parcial"
    assert indicador.valor["organizaciones_con_datos_completos"] == 0
    assert indicador.valor["organizaciones_totales"] == 3
    assert "años" in indicador.explicacion.lower() or "período" in indicador.explicacion.lower() \
        or "mezcla" in indicador.explicacion.lower()


def test_una_organizacion_con_las_3_consultas_calcula_su_tasa(sesion):
    importador = VisocPorSolicitante()
    importador.mapear(importador.lectura_desde_lineas(LINEAS_PS, consulta="solicitadas"),
                      sesion, _importacion(sesion, "1" * 64))
    importador.mapear(importador.lectura_desde_lineas(LINEAS_PS, consulta="activadas"),
                      sesion, _importacion(sesion, "2" * 64))
    importador.mapear(importador.lectura_desde_lineas(LINEAS_PS, consulta="finalizadas"),
                      sesion, _importacion(sesion, "3" * 64))
    sesion.commit()

    indicador = tasa_activacion_finalizacion(FuentePropia(sesion=sesion))
    assert indicador.valor["organizaciones_con_datos_completos"] == 3
    fila = next(f for f in indicador.valor["por_organizacion"] if f["nombre"] == "MUNICIPALIDAD DE VILLA EJEMPLO")
    # LINEAS_PS: esa organización tiene solicitudes=3 (consulta solicitadas) y activadas=3 (consulta activadas)
    assert fila["solicitudes"] == 3 and fila["activadas"] == 3 and fila["tasa_activacion"] == 1.0


def test_dos_reportes_de_la_misma_consulta_usan_el_mas_nuevo_no_un_promedio(sesion):
    # Un «solicitadas» viejo (fecha 02/09/26, del fixture) y uno nuevo con otros valores para la misma
    # organización. No debe promediarlos ni quedarse con el que se importó último por casualidad.
    viejo = LINEAS_PS
    nuevo = [l.replace("MUNICIPALIDAD DE VILLA EJEMPLO 3 9 3 3", "MUNICIPALIDAD DE VILLA EJEMPLO 6 18 3 3")
            .replace("Fecha: 02/09/26", "Fecha: 01/01/27")
            .replace("INTENDENCIA 3 9 3 3", "INTENDENCIA 6 18 3 3")
            .replace("TOTAL GRAL 6 17 4 3", "TOTAL GRAL 9 26 4 3") for l in LINEAS_PS]

    # El «solicitadas» nuevo se carga PRIMERO (por ejemplo, al completar después un archivo histórico
    # que faltaba): el resultado no debe depender del orden en que se cargaron los archivos.
    importador = VisocPorSolicitante()
    importador.mapear(importador.lectura_desde_lineas(nuevo, consulta="solicitadas"),
                      sesion, _importacion(sesion, "4" * 64, fecha_reporte=date(2027, 1, 1)))
    importador.mapear(importador.lectura_desde_lineas(viejo, consulta="solicitadas"),
                      sesion, _importacion(sesion, "1" * 64))
    importador.mapear(importador.lectura_desde_lineas(viejo, consulta="activadas"),
                      sesion, _importacion(sesion, "2" * 64))
    importador.mapear(importador.lectura_desde_lineas(viejo, consulta="finalizadas"),
                      sesion, _importacion(sesion, "3" * 64))
    sesion.commit()

    indicador = tasa_activacion_finalizacion(FuentePropia(sesion=sesion))
    fila = next(f for f in indicador.valor["por_organizacion"] if f["nombre"] == "MUNICIPALIDAD DE VILLA EJEMPLO")
    assert fila["solicitudes"] == 6   # el reporte nuevo, no 3 (el viejo) ni 4.5 (el promedio)


def test_la_explicacion_aclara_que_las_organizaciones_ausentes_quedan_afuera_no_en_cero(sesion):
    # Decisión del Review Focus del Plan 3, punto 2: una organización sin datos en las 3 consultas queda
    # fuera del cálculo (no se le asume 0 %). Esto puede ocultar organizaciones con mal desempeño, así
    # que el texto tiene que decirlo en vez de dejarlo implícito.
    indicador = tasa_activacion_finalizacion(FuentePropia(sesion=sesion))
    assert "ausente" in indicador.explicacion.lower() or "no aparece" in indicador.explicacion.lower()
