from datetime import date, datetime

from datos.fuentes.propia import FuentePropia
from datos.fuentes.simulada import FuenteSimulada
from datos.importadores.visoc_por_solicitante import VisocPorSolicitante
from datos.indicadores.tipo_solicitante import peso_tipo_solicitante
from datos.modelo import Importacion
from tests.fixtures_visoc import LINEAS_PS


def _importacion(sesion, fecha_reporte=date(2026, 9, 2), huella="0" * 64):
    # `fecha_reporte` va acá porque en producción lo pone `importar_archivo` (Plan 1) al leer la línea
    # «Fecha:» del reporte; estas pruebas arman la importación a mano, sin pasar por ese camino.
    imp = Importacion(tipo_reporte="visoc_por_solicitante", archivo_nombre="x", archivo_huella=huella,
                      estado="leida", fecha_reporte=fecha_reporte, importado_en=datetime.now())
    sesion.add(imp)
    sesion.flush()
    return imp


def test_sin_datos_queda_no_disponible(sesion):
    indicador = peso_tipo_solicitante(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "no_disponible"


def test_con_el_pie_de_ejemplo_calcula_el_peso_por_solicitudes(sesion):
    importador = VisocPorSolicitante()
    importador.mapear(importador.lectura_desde_lineas(LINEAS_PS), sesion, _importacion(sesion))
    sesion.commit()

    indicador = peso_tipo_solicitante(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "disponible"
    # LINEAS_PS: COOPERATIVA 2, ASOCIACION_ONG 1, INTENDENCIA 3 (de 6 solicitudes en total)
    assert indicador.valor["solicitudes"]["COOPERATIVA"] == 2
    assert indicador.valor["solicitudes"]["INTENDENCIA"] == 3
    assert sum(indicador.valor["solicitudes"].values()) == 6


def test_real_solicitadas_da_los_totales_verificados(real, sesion):
    from datos.importadores.pdf import leer_lineas_texto
    importador = VisocPorSolicitante()
    lectura = importador.lectura_desde_lineas(leer_lineas_texto(real("solicitadas")))
    importador.mapear(lectura, sesion, _importacion(sesion))
    sesion.commit()

    indicador = peso_tipo_solicitante(FuentePropia(sesion=sesion))
    assert indicador.valor["solicitudes"] == {"COOPERATIVA": 304, "ASOCIACION_ONG": 507,
                                              "COMISIONADO": 239, "INTENDENCIA": 59, "EXTERNA": 0}


def test_no_esta_disponible_con_la_fuente_simulada():
    indicador = peso_tipo_solicitante(FuenteSimulada())
    assert indicador.capacidad == "no_disponible"


def test_dos_reportes_de_la_misma_consulta_usan_el_pie_mas_nuevo(sesion):
    viejo = LINEAS_PS
    nuevo = [l.replace("INTENDENCIA 3 9 3 3", "INTENDENCIA 6 18 3 3")
            .replace("Fecha: 02/09/26", "Fecha: 01/01/27")
            .replace("TOTAL GRAL 6 17 4 3", "TOTAL GRAL 9 26 4 3") for l in LINEAS_PS]

    # Se cargan en orden inverso al de la fecha (primero el nuevo, después el viejo, por ejemplo al
    # completar un archivo histórico que faltaba): el resultado no debe depender de ese orden.
    importador = VisocPorSolicitante()
    imp_nuevo = _importacion(sesion, fecha_reporte=date(2027, 1, 1), huella="1" * 64)
    importador.mapear(importador.lectura_desde_lineas(nuevo), sesion, imp_nuevo)
    importador.mapear(importador.lectura_desde_lineas(viejo), sesion, _importacion(sesion))
    sesion.commit()

    indicador = peso_tipo_solicitante(FuentePropia(sesion=sesion))
    assert indicador.valor["solicitudes"]["INTENDENCIA"] == 6   # el pie del reporte nuevo, no el viejo (3)
