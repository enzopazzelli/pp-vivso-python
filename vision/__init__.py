"""
Verificación fotográfica del AFO — componente de Ciencia de Datos.

Usa las fotos que adjunta la gestora para **ponderar su reporte de avance**, nunca
para aprobarlo: el AFO lo sigue certificando el técnico. El diseño completo está en
docs/vision-afo.md y los supuestos en docs/supuestos-abiertos.md.

Arquitectura en dos capas, y la separación es deliberada:

    percepcion.py  →  evidencia física observable   (modelo de visión, o simulación)
    decision.py    →  rubro → AFO → grado de respaldo (regla determinista)

El modelo no estima el porcentaje: estima la evidencia. La aritmética la hace el
catálogo de rubros que ya existe. Eso es lo que permite decirle a una gestora "la foto
muestra muros con encadenado y sin revoque, entonces rubro 5, entonces 33%" en vez de
un número sin explicación — el mismo criterio con el que se defendió el modelo de riesgo.

Estado: corre entero sin API y sin fotos, con percepción simulada. Ver `python -m vision.demo`.
"""
from vision.decision import ETIQUETA_GRADO, Lectura, explicar, grado_de_respaldo, leer_evidencia
from vision.esquema import EVIDENCIA_SCHEMA
from vision.percepcion import PercepcionClaude, PercepcionSimulada, evidencia_ideal
from vision.rubrica import EVIDENCIA_OBSERVABLE, RUBROS_VENTANA_TEMPORAL, prompt_sistema

__all__ = [
    "EVIDENCIA_OBSERVABLE", "EVIDENCIA_SCHEMA", "ETIQUETA_GRADO", "Lectura",
    "PercepcionClaude", "PercepcionSimulada", "RUBROS_VENTANA_TEMPORAL",
    "evidencia_ideal", "explicar", "grado_de_respaldo", "leer_evidencia", "prompt_sistema",
]
