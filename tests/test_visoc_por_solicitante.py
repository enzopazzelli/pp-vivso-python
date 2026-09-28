from datetime import date, datetime

from datos.importadores.visoc_por_solicitante import (
    VisocPorSolicitante, inferir_consulta, parsear_por_solicitante, reconoce_lineas,
)
from datos.modelo import Importacion, MedidaOrganizacion
from db.models import Organizacion
from tests.fixtures_visoc import LINEAS_PS


def _importacion(sesion):
    imp = Importacion(tipo_reporte="visoc_por_solicitante", archivo_nombre="x.pdf", archivo_huella="0" * 64,
                      estado="leida", importado_en=datetime.now())
    sesion.add(imp)
    sesion.flush()
    return imp


def test_parsear_lee_parametros_filas_y_pie():
    parametros, filas, pie = parsear_por_solicitante(LINEAS_PS)
    assert parametros == {"fecha_reporte": "2026-09-02", "periodo_desde": "2026-01-01", "periodo_hasta": "2026-09-01"}
    assert [f["nombre"] for f in filas] == [
        "MUNICIPALIDAD DE VILLA EJEMPLO", "ASOC. CIVIL ESPERANZA", "COOP.DE TRABAJO LOS PINOS"]
    assert filas[0] == {"nombre": "MUNICIPALIDAD DE VILLA EJEMPLO", "solicitudes": 3, "beneficiarios": 9,
                        "activadas": 3, "fin_obras": 3}
    assert pie["COOPERATIVA"] == (2, 5, 0, 0) and pie["TOTAL GRAL"] == (6, 17, 4, 3)


def test_los_numeros_con_punto_de_miles_se_leen_bien():
    parametros, filas, pie = parsear_por_solicitante(["ASOC. X 1.234 3.461 162 140"])
    assert (filas[0]["solicitudes"], filas[0]["beneficiarios"]) == (1234, 3461)


def test_inferir_consulta_por_los_datos():
    def fila(s, a, f):
        return {"solicitudes": s, "activadas": a, "fin_obras": f}
    assert inferir_consulta([fila(2, 2, 2), fila(1, 1, 1)]) == "finalizadas"
    assert inferir_consulta([fila(2, 2, 1), fila(1, 1, 0)]) == "activadas"
    assert inferir_consulta([fila(2, 1, 0), fila(1, 0, 0)]) == "solicitadas"


def test_reconoce_el_formato_por_su_cabecera():
    assert reconoce_lineas(LINEAS_PS) == 0.95
    assert reconoce_lineas(["Viviendas Segun Solicitante Desarrollo Social", "Fecha: 31/10/25"]) == 0.0
    assert reconoce_lineas([]) == 0.0


def test_la_lectura_infiere_la_consulta_y_valida():
    importador = VisocPorSolicitante()
    lectura = importador.lectura_desde_lineas(LINEAS_PS)
    assert lectura.parametros["consulta"] == "solicitadas" and lectura.parametros["consulta_inferida"] is True
    assert lectura.fecha_reporte == date(2026, 9, 2) and lectura.advertencias == []
    validacion = importador.validar(lectura)
    assert validacion.ok, [c for c in validacion.chequeos if not c.ok]


def test_se_puede_indicar_la_consulta():
    lectura = VisocPorSolicitante().lectura_desde_lineas(LINEAS_PS, consulta="activadas")
    assert lectura.parametros["consulta"] == "activadas" and lectura.parametros["consulta_inferida"] is False


def test_una_fila_perdida_hace_fallar_la_validacion():
    lineas = [l for l in LINEAS_PS if "COOP.DE TRABAJO" not in l]
    importador = VisocPorSolicitante()
    validacion = importador.validar(importador.lectura_desde_lineas(lineas))
    assert not validacion.ok
    assert "suma_solicitudes" in [c.nombre for c in validacion.chequeos if not c.ok]


def test_sin_pie_no_se_puede_validar():
    lineas = [l for l in LINEAS_PS if l.split()[0] not in ("COOPERATIVA", "ASOCIACION/ONG", "COMISIONADO", "INTENDENCIA")]
    importador = VisocPorSolicitante()
    validacion = importador.validar(importador.lectura_desde_lineas(lineas))
    assert not validacion.ok and validacion.chequeos[-1].nombre == "pie_presente"


def test_un_total_gral_que_no_coincide_es_advertencia_y_no_error():
    lineas = ["TOTAL GRAL 99 17 4 3" if l.startswith("TOTAL GRAL") else l for l in LINEAS_PS]
    importador = VisocPorSolicitante()
    lectura = importador.lectura_desde_lineas(lineas)
    assert lectura.advertencias and "TOTAL GRAL" in lectura.advertencias[0]
    assert importador.validar(lectura).ok


def test_mapear_crea_organizaciones_y_medidas(sesion):
    importador = VisocPorSolicitante()
    lectura = importador.lectura_desde_lineas(LINEAS_PS)
    importador.mapear(lectura, sesion, _importacion(sesion))
    sesion.commit()

    assert sesion.query(Organizacion).count() == 3
    assert sesion.query(MedidaOrganizacion).count() == 12   # 3 organizaciones x 4 métricas
    organizacion = sesion.query(Organizacion).filter_by(nombre="MUNICIPALIDAD DE VILLA EJEMPLO").one()
    assert organizacion.tipo_gestora == "Municipio"
    medida = (sesion.query(MedidaOrganizacion)
              .filter_by(cuit=organizacion.cuit, metrica="activadas").one())
    assert medida.valor == 3 and medida.consulta == "solicitadas"
    assert medida.periodo_desde == date(2026, 1, 1) and medida.periodo_hasta == date(2026, 9, 1)


def test_mapear_guarda_el_pie_por_categoria(sesion):
    from datos.modelo import MedidaCategoria
    importador = VisocPorSolicitante()
    lectura = importador.lectura_desde_lineas(LINEAS_PS)
    importador.mapear(lectura, sesion, _importacion(sesion))
    sesion.commit()

    filas = sesion.query(MedidaCategoria).filter_by(tipo_solicitante="COOPERATIVA").all()
    por_metrica = {f.metrica: f.valor for f in filas}
    assert por_metrica == {"solicitudes": 2, "beneficiarios": 5, "activadas": 0, "fin_obras": 0}
    assert all(f.consulta == "solicitadas" for f in filas)
    # EXTERNA vale 0 en el pie de LINEAS_PS, pero igual se guarda (no se omite lo que da cero)
    externa = sesion.query(MedidaCategoria).filter_by(tipo_solicitante="EXTERNA").count()
    assert externa == 4


def test_real_el_pie_de_solicitadas_guarda_los_totales_reales(real, sesion):
    from datos.importadores.pdf import leer_lineas_texto
    from datos.modelo import MedidaCategoria

    importador = VisocPorSolicitante()
    lectura = importador.lectura_desde_lineas(leer_lineas_texto(real("solicitadas")))
    importador.mapear(lectura, sesion, _importacion(sesion))
    sesion.commit()

    esperado = {"COOPERATIVA": (304, 926, 37, 32), "ASOCIACION_ONG": (507, 1580, 80, 66),
               "COMISIONADO": (239, 733, 37, 34), "INTENDENCIA": (59, 222, 8, 8), "EXTERNA": (0, 0, 0, 0)}
    for codigo, (solicitudes, beneficiarios, activadas, fin_obras) in esperado.items():
        por_metrica = {f.metrica: f.valor for f in
                       sesion.query(MedidaCategoria).filter_by(tipo_solicitante=codigo).all()}
        assert por_metrica == {"solicitudes": solicitudes, "beneficiarios": beneficiarios,
                               "activadas": activadas, "fin_obras": fin_obras}, codigo


def test_real_los_tres_reportes_cierran_con_su_pie(real):
    from datos.importadores.pdf import leer_lineas_texto
    esperado = {"solicitadas": ("solicitadas", 715), "activadas": ("activadas", 704), "finalizadas": ("finalizadas", 685)}
    importador = VisocPorSolicitante()
    for nombre, (consulta, filas) in esperado.items():
        lectura = importador.lectura_desde_lineas(leer_lineas_texto(real(nombre)))
        assert lectura.parametros["consulta"] == consulta, nombre
        assert len(lectura.filas) == filas, nombre
        assert importador.validar(lectura).ok, nombre
