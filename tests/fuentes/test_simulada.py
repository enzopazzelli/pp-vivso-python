from datos.fuentes.estructura import COLUMNAS_ORGANIZACION, COLUMNAS_VIVIENDA
from datos.fuentes.simulada import FuenteSimulada


def test_lee_los_csv_reales_de_pp2_sin_modificarlos():
    fuente = FuenteSimulada()
    viviendas = fuente.viviendas()
    assert list(viviendas.columns) == COLUMNAS_VIVIENDA
    assert len(viviendas) == 5000   # data/viviendas_sinteticas.csv
    assert viviendas["expediente"].iloc[0] == viviendas["num_exp"].iloc[0]
    assert viviendas["titular_seudonimo"].isna().all()   # PP2 nunca modeló este concepto

    organizaciones = fuente.organizaciones()
    assert list(organizaciones.columns) == COLUMNAS_ORGANIZACION
    assert len(organizaciones) == 8   # data/organizaciones.csv
    assert organizaciones["cuit_provisional"].eq(False).all()
    assert organizaciones["nombre_normalizado"].notna().all()


def test_medidas_y_reclamos_estan_vacios_pero_con_columnas():
    fuente = FuenteSimulada()
    assert fuente.medidas().empty and fuente.reclamos().empty


def test_expedientes_se_derivan_del_num_exp():
    fuente = FuenteSimulada()
    expedientes = fuente.expedientes()
    assert len(expedientes) == 5000
    assert set(expedientes["tipo"].unique()) == {"solicitud"}
    assert set(expedientes["formato"].unique()) == {"desconocido"}   # «SIM-2025-0001» no es un formato real


def test_sin_los_archivos_devuelve_marcos_vacios_con_las_columnas_correctas(tmp_path):
    fuente = FuenteSimulada(carpeta_datos=tmp_path)
    assert fuente.viviendas().empty and list(fuente.viviendas().columns) == COLUMNAS_VIVIENDA
    assert fuente.organizaciones().empty and list(fuente.organizaciones().columns) == COLUMNAS_ORGANIZACION


def test_prefiere_viviendas_procesadas_si_existe(tmp_path):
    import pandas as pd

    columnas_pp2 = ["num_exp", "departamento", "localidad", "barrio", "direccion", "superficie",
                    "fecha_inic", "fecha_fin", "estado", "lat", "lng", "avance_obra", "clasificacion",
                    "criterio", "tipo_vivienda", "cant_dormitorios", "observacion", "id_familia",
                    "representante", "cuit_org", "nivel_riesgo", "cluster", "dias_activa"]
    fila = {c: "x" if c in ("num_exp", "departamento", "estado") else None for c in columnas_pp2}
    fila.update(num_exp="proc-1", departamento="Capital", estado="Finalizada")
    pd.DataFrame([fila]).to_csv(tmp_path / "viviendas_procesadas.csv", index=False)
    pd.DataFrame([fila]).assign(num_exp="sint-1").to_csv(tmp_path / "viviendas_sinteticas.csv", index=False)

    fuente = FuenteSimulada(carpeta_datos=tmp_path)
    assert fuente.viviendas()["num_exp"].tolist() == ["proc-1"]


def test_medidas_categoria_y_fecha_activacion_no_estan_en_pp2():
    fuente = FuenteSimulada()
    assert fuente.medidas_categoria().empty
    assert fuente.viviendas()["fecha_activacion"].isna().all()
