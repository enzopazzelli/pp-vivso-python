"""
Encuadre fijo del mapa de Santiago del Estero, compartido por todas las páginas.

Antes cada mapa dejaba que Plotly calculara el centro solo, a partir del promedio
de lo que estuviera graficado. Con filtros aplicados (por ejemplo, un solo
departamento chico), ese centro se recalcula y el mapa "salta" a otra zona sin
aviso — y con un zoom fijo de 6 (heredado, sin centro fijo) se ve más territorio
del que hace falta: a ese zoom, un mapa de ~800px de ancho muestra ~17,6° de
longitud, casi 5 veces el ancho real de la provincia (~3,2°). El resultado es
que el mapa parece "estar en cualquier lado" en vez de leerse como Santiago del
Estero. Fijar centro y zoom para toda la app resuelve las dos cosas a la vez.

El centro es el centroide de `LOCALIDADES` ponderado por `peso` (población),
calculado una vez sobre synthetic/generate.py — no se importa ese módulo acá
porque carga Faker y el resto del generador solo para leer dos números.
"""

# Centroide ponderado por población de synthetic.generate.LOCALIDADES.
# Recalcular con la fórmula si el catálogo de localidades cambia:
#   sum(lat*peso)/sum(peso), sum(lng*peso)/sum(peso)
CENTRO_PROVINCIA = {"lat": -28.04, "lon": -63.73}

# Encuadra la provincia completa (18 departamentos, ~3,2° de longitud por
# ~3,7° de latitud) con margen, sin llegar a verse como el norte argentino entero.
ZOOM_PROVINCIA = 6.7
