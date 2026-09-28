from datetime import datetime

from datos.fuentes.propia import FuentePropia
from datos.importadores.visoc_viviendas import VisocViviendasSegunSolicitante
from datos.indicadores.tiempos import tiempos_del_proceso
from datos.modelo import Importacion
from tests.fixtures_visoc import LINEAS_V


def _importacion(sesion):
    imp = Importacion(tipo_reporte="visoc_viviendas_segun_solicitante", archivo_nombre="x",
                      archivo_huella="0" * 64, estado="leida", importado_en=datetime.now())
    sesion.add(imp)
    sesion.flush()
    return imp


def test_sin_datos_queda_no_disponible(sesion):
    indicador = tiempos_del_proceso(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "no_disponible"


def test_calcula_dias_de_solicitud_a_activacion_y_de_activacion_a_fin(sesion, anon):
    VisocViviendasSegunSolicitante().mapear(
        VisocViviendasSegunSolicitante().lectura_desde_lineas(LINEAS_V, anon), sesion, _importacion(sesion))
    sesion.commit()

    indicador = tiempos_del_proceso(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "disponible"
    # La vivienda 2128915-2022: solicitud 07/06/22, activación 04/12/23 -> 545 días
    assert indicador.valor["solicitud_a_activacion"]["cantidad"] >= 1
    assert indicador.valor["solicitud_a_activacion"]["dias_minimo"] > 0
    # activación 04/12/23, fin 06/12/23 -> 2 días
    assert indicador.valor["activacion_a_fin_obra"]["dias_minimo"] >= 0
