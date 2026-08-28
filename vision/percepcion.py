"""
Capa de percepción: de una foto (o de una simulación) a evidencia física observable.

Hay dos implementaciones y NO son intercambiables — decirlo explícito evita confusiones:

- `PercepcionSimulada` no mira fotos. Genera la evidencia que un modelo *debería*
  reportar para una obra de avance conocido y la degrada con una tasa de error
  configurable. Existe para poder medir la capa de decisión y el harness de evaluación
  **sin una sola foto y sin conectarse a ninguna API**, que es exactamente el estado
  del proyecto hoy. Y habilita el resultado que sí se puede presentar ahora: cuán
  bueno tiene que ser el modelo real para que el sistema sirva.

- `PercepcionClaude` es el adaptador real. Está escrito y completo, pero todavía no se
  ejercitó: necesita ANTHROPIC_API_KEY y fotos. Cuando lleguen, se enchufa sin tocar
  nada más — la capa de decisión consume el mismo diccionario de evidencia.
"""
import base64
import json
import os
import random
from pathlib import Path

from vision.esquema import EVIDENCIA_SCHEMA, lectura_no_util
from vision.rubrica import (
    CAMPOS_EVIDENCIA,
    NO_DETERMINABLE,
    prompt_sistema,
)

MODELO = "claude-opus-5"


# ═══════════════════════════════════════════════════════════════════════════
# Simulación — funciona hoy, sin API y sin fotos
# ═══════════════════════════════════════════════════════════════════════════

def evidencia_ideal(rubro_alcanzado: int, ocultar_ventanas: bool = True) -> dict:
    """
    La evidencia que una foto perfecta mostraría para una obra en `rubro_alcanzado`.

    Es la inversa de la regla de decision.py: cada campo toma el valor que confirma
    todos los rubros hasta el alcanzado y descarta el siguiente. Sirve de verdad de
    referencia contra la cual medir una lectura degradada.

    `ocultar_ventanas` modela una limitación física real, no un error del modelo: la
    capa aisladora del rubro 2 queda enterrada al rellenar la excavación, así que una
    obra que ya la pasó no puede mostrarla por más buena que sea la foto. Simularlo
    importa, porque es justo el caso que obliga a la capa de decisión a inferir los
    rubros tapados a partir de los posteriores.
    """
    a = rubro_alcanzado
    evidencia = {
        "terreno":               "despejado" if a >= 1 else "sin_preparar",
        "capa_aisladora":        "si" if a >= 2 else "no",
        "muros":                 ("completo" if a >= 4 else
                                  "hasta_dintel" if a == 3 else
                                  "fundacion" if a == 2 else "ninguno"),
        "encadenado":            "si" if a >= 5 else "no",
        "revoque_int":           "fino" if a >= 6 else "ninguno",
        "revoque_ext":           "fino" if a >= 7 else "ninguno",
        "cielorraso":            ("terminado" if a >= 9 else
                                  "estructura" if a == 8 else "ninguno"),
        "aberturas":             "colocadas" if a >= 10 else "vanos_vacios",
        "tanque_agua":           "si" if a >= 11 else "no",
        "tablero_electrico":     "completo" if a >= 12 else "ninguno",
        "artefactos_sanitarios": "completos" if a >= 13 else "ninguno",
        "revestimiento_ext":     "terminado" if a >= 14 else "ninguno",
    }
    if ocultar_ventanas and a > 2:
        evidencia["capa_aisladora"] = NO_DETERMINABLE   # ya está tapada
    return evidencia


class PercepcionSimulada:
    """
    Modelo de visión simulado con una tasa de error controlada.

    `tasa_error` es la probabilidad de que un campo salga mal. De esos errores, una
    parte sale como abstención ('no_determinable') y el resto como valor equivocado:
    un modelo real se equivoca de las dos formas, y no cuestan lo mismo — abstenerse
    frena la lectura, equivocarse la desvía.
    """

    def __init__(self, tasa_error: float = 0.0, prop_abstencion: float = 0.5, seed: int = 42):
        self.tasa_error = tasa_error
        self.prop_abstencion = prop_abstencion
        self.rng = random.Random(seed)

    def leer_desde_verdad(self, rubro_alcanzado: int) -> dict:
        ideal = evidencia_ideal(rubro_alcanzado)
        return {campo: self._degradar(campo, valor) for campo, valor in ideal.items()}

    def _degradar(self, campo: str, valor: str) -> str:
        if self.rng.random() >= self.tasa_error:
            return valor
        if self.rng.random() < self.prop_abstencion:
            return NO_DETERMINABLE
        # Valor equivocado: cualquiera de los otros admitidos para ese campo.
        alternativas = [v for v in CAMPOS_EVIDENCIA[campo] if v != valor]
        return self.rng.choice(alternativas) if alternativas else NO_DETERMINABLE


# ═══════════════════════════════════════════════════════════════════════════
# Adaptador real — escrito, todavía sin ejercitar
# ═══════════════════════════════════════════════════════════════════════════

class PercepcionClaude:
    """
    Lee una foto real con un modelo de visión y devuelve el checklist de evidencia.

    Dos decisiones que importan:
    - **Salida estructurada**, no texto libre: el esquema obliga al modelo a responder
      sobre los campos de la rúbrica y a poder abstenerse. Sin eso volveríamos a
      interpretar prosa, que es lo que hace irreproducible a un pipeline.
    - **La rúbrica va cacheada** en el prompt de sistema. Es estable y larga; se paga
      una vez y se reutiliza en todas las fotos del lote.
    """

    def __init__(self, modelo: str = MODELO, api_key: str | None = None):
        self.modelo = modelo
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._cliente = None

    def _obtener_cliente(self):
        # Import perezoso a propósito: todo el resto del componente —simulación,
        # decisión, evaluación, dashboard— tiene que funcionar sin el paquete
        # instalado y sin credenciales. Solo este camino los necesita.
        if self._cliente is None:
            try:
                import anthropic
            except ImportError as e:
                raise RuntimeError(
                    "Falta el paquete 'anthropic'. Instalalo con: pip install anthropic"
                ) from e
            if not self._api_key:
                raise RuntimeError(
                    "Falta ANTHROPIC_API_KEY. Ponela en el .env o exportala en el entorno."
                )
            self._cliente = anthropic.Anthropic(api_key=self._api_key)
        return self._cliente

    def leer_foto(self, ruta: str | Path, contexto: str = "") -> dict:
        """
        Devuelve el diccionario completo de lectura (tipo_toma, evidencia, confianza,
        observaciones). `contexto` sirve para pasarle el último rubro verificado de la
        obra: no para que lo copie, sino para que sepa qué esperar.
        """
        # Las credenciales se validan primero: si faltan, conviene que el error lo diga
        # en vez de quedar tapado por un "archivo no encontrado" del lote de fotos.
        cliente = self._obtener_cliente()

        ruta = Path(ruta)
        media = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".webp": "image/webp"}.get(ruta.suffix.lower())
        if media is None:
            return lectura_no_util(f"Formato de imagen no soportado: {ruta.suffix}")

        datos = base64.standard_b64encode(ruta.read_bytes()).decode("utf-8")

        respuesta = cliente.messages.create(
            model=self.modelo,
            max_tokens=2000,
            thinking={"type": "adaptive"},
            cache_control={"type": "ephemeral"},   # la rúbrica es estable entre fotos
            system=prompt_sistema(),
            output_config={"format": {"type": "json_schema", "schema": EVIDENCIA_SCHEMA}},
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image",
                     "source": {"type": "base64", "media_type": media, "data": datos}},
                    {"type": "text", "text": contexto or "Analizá esta foto de obra."},
                ],
            }],
        )

        texto = next((b.text for b in respuesta.content if b.type == "text"), "")
        # El SDK puede devolver escapes distintos según el modelo: parsear siempre,
        # nunca hacer coincidencias de texto sobre el JSON serializado.
        return json.loads(texto)
