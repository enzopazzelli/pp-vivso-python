# Flujo de trabajo del Programa de Viviendas Sociales

Esta es la versión en Mermaid del diagrama de flujo que armó el área (*Diagrama de flujo del Programa
de Viviendas Sociales*, versión 6). Muestra el recorrido de una solicitud por los dos sistemas que
usa hoy el programa:

- **VISOC**, donde se registra el expediente y se sigue la obra.
- **GDO**, donde se tramita el expediente administrativo. El diagrama lo llama GDO; en el resto de
  la documentación del proyecto lo llamamos **GDE** (el sistema de expedientes electrónicos).
  Entendemos que es el mismo sistema; queda para confirmar con el área.

El PDF original está en la carpeta local `pantallas/`, junto con las capturas de pantalla de VISOC.
Esa carpeta no se sube al repositorio porque las capturas muestran datos personales reales.

## Diagrama

```mermaid
flowchart TB
    subgraph VISOC["SISTEMA VISOC · Registro de expediente"]
        subgraph F1["1 · Registro de expediente"]
            direction LR
            DOC["Documentación"]
            TIT["Titular"]
            GF["Grupo familiar"]
            INST["Institución solicitante<br/>(solo OG u ONG)"]
            OG["OG · Organización gubernamental<br/>viviendas ecológicas"]
            ONG["ONG<br/>viviendas urbanas"]
            CM["Comisión Municipal"]
            INTE["Intendencia"]
            PJ["Institución con<br/>personería jurídica"]
            PROTO["Prototipo de vivienda"]
            ECO["Ecológica<br/>con OG"]
            URB["Urbana<br/>con ONG"]
            BD["Consulta base de datos<br/>(Munidigital)"]
            ANT["Antecedentes habitacionales"]
            Q1{"¿Es adjudicatario?"}
            Q2{"¿Es solicitante?"}
            SIN["No posee antecedentes"]
            R1["Rechaza solicitud"]
            R2["Rechaza solicitud"]
            FA1["Factible"]
            FA2["Factible"]
            FA3["Factible"]
        end
        subgraph F2["2 · Visita previa"]
            REL["Relevamiento técnico"]
            CLA["Clasificación de la vivienda"]
            PA["PRE APTO"]
            NA["NO APTO"]
            OT["OTROS"]
        end
        subgraph F3["3 · Activación del expediente al usuario del técnico"]
            direction LR
            SUP["Supervisión de obra"]
            FIN{"¿Obra finalizada?"}
            ACTA["Generar acta de finalización"]
            MOB["Mobiliario"]
        end
    end

    subgraph GDO["SISTEMA GDO · Registro de información"]
        G1["1 · Caratulación de expediente"]
        G2["2 · Creación de notas"]
        G3["3 · Análisis y trazabilidad del expediente"]
        AP["APROBADO"]
        DES["DESAPROBADO"]
        G4["4 · Resolución ministerial"]
        NOTA["El GDO acompaña la gestión del<br/>expediente tramitado en VISOC"]
    end

    DOC --> TIT & GF & INST
    INST --> OG & ONG
    OG --> CM & INTE
    ONG --> PJ
    INST -->|sugiere| PROTO
    PROTO --> ECO & URB
    DOC --> BD --> ANT
    ANT --> Q1 & Q2 & SIN
    Q1 -->|Sí| R1
    Q1 -->|No| FA1
    Q2 -->|Sí| R2
    Q2 -->|No| FA2
    SIN --> FA3

    REL --> CLA --> PA & NA & OT

    SUP --> FIN
    FIN -->|No| SUP
    FIN -->|Sí| ACTA --> MOB

    G1 --> G2 --> G3 --> AP --> G4
    G4 ~~~ NOTA

    PA --> AP
    NA --> DES

    F1 -.-> F2 -.-> F3
    OT ~~~ F3

    classDef favorable fill:#dcfce7,stroke:#15803d,color:#14532d
    classDef rechazo fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d
    classDef otros fill:#ffedd5,stroke:#c2410c,color:#7c2d12
    classDef externa fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a
    classDef og fill:#ccfbf1,stroke:#0f766e,color:#134e4a
    classDef ong fill:#fef3c7,stroke:#b45309,color:#78350f
    classDef gdo fill:#ede9fe,stroke:#6d28d9,color:#4c1d95
    class FA1,FA2,FA3,PA,AP,ACTA favorable
    class R1,R2,NA,DES rechazo
    class OT otros
    class BD,ANT,NOTA externa
    class OG,ECO og
    class ONG,URB ong
    class G1,G2,G3,G4 gdo
    style VISOC fill:#fdf2f8,stroke:#be185d,color:#831843
    style GDO fill:#f5f3ff,stroke:#6d28d9,color:#4c1d95
    style F1 fill:none,stroke:#f9a8d4,color:#831843
    style F2 fill:none,stroke:#f9a8d4,color:#831843
    style F3 fill:none,stroke:#f9a8d4,color:#831843
```

## Cómo leerlo

- **Colores**, los mismos del original: verde para un resultado favorable, rojo para un rechazo o
  una vivienda no apta, naranja para otros casos y azul para una consulta a otro sistema. En el
  original, el verde azulado y el ámbar indican qué prototipo va con cada tipo de institución: la
  vivienda ecológica con una OG y la urbana con una ONG.
- **Las tres fases de VISOC** están numeradas como en el original. El PDF no dibuja flechas entre
  una fase y la siguiente. Las flechas punteadas se agregaron acá solo para marcar ese orden.
- **Las dos flechas que cruzan de un sistema al otro** sí están en el original. Si en la visita
  previa la vivienda resulta *pre apta*, eso acompaña la aprobación en GDO. Si resulta *no apta*,
  lleva a la desaprobación.

## Dónde se ve cada paso en VISOC

Las capturas de pantalla de VISOC permiten ubicar cada paso del diagrama en una pantalla concreta.
El modelo de datos que armamos a partir de ellas está en [modelo-de-datos.md](modelo-de-datos.md).

| Paso del diagrama | Pantalla de VISOC | Qué se registra |
| :--- | :--- | :--- |
| Registro de expediente | «Seleccione un Expediente» y ficha del expediente | Número, fecha y organización solicitante. Un expediente agrupa varias viviendas. |
| Documentación: titular y grupo familiar | Ficha de la vivienda y «Grupo Familiar» | Titular e integrantes: DNI, nombre, año de nacimiento («Clase») y si es titular o familiar |
| Documentación: institución solicitante | «Solicitantes» y «Autoridades» | Tipo, personería jurídica, CUIT, estado y autoridades de cada período |
| Consulta a Munidigital | No aparece: es otro sistema | — |
| Visita previa y clasificación | «Inspección Previa» | Fecha, técnico, clasificación (código y criterio), tipo de vivienda y ubicación |
| Activación | «Activación» del expediente | Estado, tipo de vivienda, dormitorios, monto, técnico del acta y números de expediente de activación y de reconsideración |
| Supervisión de obra | «Avance de Obra» e «Inspección Técnica» | Hasta 4 inspecciones, con el porcentaje de cada uno de los 17 rubros y el avance total (AFO) |
| ¿Obra finalizada? | «Fin de Obra» | Fecha y número de resolución |
| Acta de finalización | «Acta Recepción» (acta digital) | Número de expediente del acta y técnico |
| Mobiliario | «Acta Mobiliario» | No vimos esta pantalla abierta |
| Trámite en GDO | No hay capturas | — |

VISOC registra además cosas que el diagrama no muestra: la suspensión y la reactivación de una
obra, la sustitución del titular, la baja, el archivo del expediente, los reclamos, los documentos
adjuntos y la agenda de trabajo de cada técnico.

## Puntos para confirmar con el área

1. **Cuándo se activa una vivienda.** El diagrama pone la activación antes de la supervisión de
   obra. Pero el 02-09-2026 el área explicó por audio que la activación se hace cuando el técnico
   certifica el 100 % de la obra, justo antes del acta (`informe_ong_og_2026/DECISIONES.md`,
   punto 13). Las dos versiones pueden ser ciertas si son dos momentos distintos: uno en que se
   asigna el técnico y otro en que se aprueba el monto. Los datos lo pueden resolver: alcanza con
   comparar la fecha de activación de cada vivienda con las fechas de sus inspecciones de avance.
2. **GDO y GDE.** Si son el mismo sistema con dos nombres.
3. **La resolución ministerial y la activación.** El diagrama no une el paso 4 de GDO con la
   activación en VISOC. Falta saber si la activación espera a la resolución.
4. **Mobiliario.** Si es un acta aparte (en VISOC hay un botón «Acta Mobiliario») o la entrega del
   mobiliario en sí.
