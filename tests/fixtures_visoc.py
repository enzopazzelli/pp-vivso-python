"""Líneas de ejemplo con la forma de los reportes reales de VISOC, con datos INVENTADOS."""

# «Por Solicitante»: 3 organizaciones. Las sumas cierran con las 4 categorías del pie.
LINEAS_PS = [
    "Por Solicitante Desarrollo Social",
    "Fecha: 02/09/26",
    "Periodo: 01/01/26 al 01/09/26",
    "Solicitante Solicitudes Beneficiarios Activadas Fin Obras",
    "MUNICIPALIDAD DE VILLA EJEMPLO 3 9 3 3",
    "ASOC. CIVIL ESPERANZA 1 3 1 0",
    "COOP.DE TRABAJO LOS PINOS 2 5 0 0",
    "COOPERATIVA 2 5 0 0",
    "ASOCIACION/ONG 1 3 1 0",
    "COMISIONADO 0 0 0 0",
    "INTENDENCIA 3 9 3 3",
    "EXTERNA 0 0 0 0",
    "TOTAL GRAL 6 17 4 3",
    "Por Solicitante Pagina:1",
]

# «Viviendas Según Solicitante»: cada línea es una lista de (texto, x0), como la entrega el lector de PDF.
# Las columnas Exp.Reclamo y Acta Digital se distinguen por su posición horizontal (521 y 599).
X_RECLAMO, X_ACTA = 521.0, 599.0


def linea(*textos):
    return [(texto, 10.0 + 12.0 * i) for i, texto in enumerate(textos)]


def fila(fecha, titular, expte, tipo, dormitorios, clasificacion, departamento,
         reclamo=None, acta=None, activacion=None, desaprobada=False, afo="0,00", fin=None):
    tokens = [(fecha, 14.0)] + [(palabra, 61.0 + 5 * i) for i, palabra in enumerate(titular.split())]
    tokens += [(expte, 277.0), (tipo, 371.0), (dormitorios, 395.0), (clasificacion, 410.0), (departamento, 428.0)]
    if reclamo:
        tokens.append((reclamo, X_RECLAMO))
    if acta:
        tokens.append((acta, X_ACTA))
    if activacion:
        tokens.append((activacion, 679.0))
    if desaprobada:
        tokens.append(("DES", 730.0))
    tokens.append((afo, 761.0))
    if fin:
        tokens.append((fin, 800.0))
    return tokens


CABECERA_V = [("Fec.Sol.", 14.0), ("Titular", 61.0), ("Expediente", 277.0), ("Tipo", 371.0), ("Drm", 395.0),
              ("Cla", 410.0), ("Departamento", 428.0), ("Exp.Reclamo", 521.0), ("Acta", 620.0),
              ("Digital", 645.0), ("Activacion", 679.0), ("AFO", 761.0), ("Fin", 790.0), ("Obra", 812.0)]

# 5 viviendas: 2 finalizadas, 1 desaprobada y 2 sin finalizar (una sin activar y otra activada).
LINEAS_V = [
    linea("Viviendas", "Segun", "Solicitante", "Desarrollo", "Social"),
    linea("Fecha:", "31/10/25"),
    linea("Solicitante", "Tipo:", "COM"),
    linea("Solicitante", "Nombre:"),
    linea("Departamento:", "Todos"),
    linea("Localidad:", "Todas"),
    linea("COMISION", "MUNICIPAL", "EJEMPLO"),
    CABECERA_V,
    fila("07/06/22", "JUANA EJEMPLO PEREZ", "2128915-2022", "URB", "2", "1A", "AVELLANEDA",
         acta="2022-00798757", activacion="04/12/23", afo="100,00", fin="06/12/23"),
    fila("07/06/22", "PEDRO MUESTRA", "2128857-2022", "RUR", "0", "1a", "AVELLANEDA"),
    fila("08/07/22", "ANA PRUEBA", "2569802-2022", "URB", "0", "2a", "AVELLANEDA", activacion="03/09/18"),
    fila("20/01/23", "LUIS DEMO", "447699-2023", "ECO", "0", "5f", "AVELLANEDA",
         activacion="28/12/23", desaprobada=True),
    fila("06/07/15", "MARTA FICTICIA", "8721-54-2015", "URB", "2", "1a", "AVELLANEDA",
         reclamo="6503", activacion="16/04/25", afo="100,00", fin="30/04/25"),
    linea("TOTALES", "COMISION", "EJEMPLO:", "Cantidad", "Solicitadas:", "5", "Cantidad", "Finalizadas:", "2",
          "Cantidad", "Desaprobadas:", "1", "Cantidad", "Sin", "Finalizar:2"),
]

NOMBRES_INVENTADOS = ("EJEMPLO", "MUESTRA", "PRUEBA", "FICTICIA", "DEMO")
