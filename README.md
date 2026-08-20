# Anatomía de una Ley

**Manual crítico del procedimiento legislativo costarricense**

**Publicado en:** <https://josoroma.github.io/anatomia-de-una-ley/>
**Repositorio:** <https://github.com/josoroma/anatomia-de-una-ley>

Obra editorial autosuficiente que integra procedimiento legislativo,
formulación de proyectos de ley, técnica legislativa, doctrina, jurisprudencia,
plantillas, checklists y análisis institucional.

---

## Contenido

| Ruta | Descripción |
|---|---|
| `capitulos/` | 26 capítulos fuente en Markdown (Apertura + Partes I–V + Cierre). |
| `herramientas/` | Plantilla de proyecto de ley + 3 checklists (presentación, validación, crítico) editables. |
| `indice.md` | Índice general. |
| `MANUAL-COMPLETO.md` | La obra completa en un solo archivo Markdown. |
| `web/` | Sitio web de lectura (SPA). |
| `web/data/libro.js` | Datos del libro generados (HTML por capítulo). |
| `web/data/plain/` | Texto plano por capítulo (insumo del audio). |
| `web/assets/audio/` | Audio por capítulo (MP3, voz natural en español). |
| `web/build.py` | *Script* que reconstruye `libro.js`, `MANUAL-COMPLETO.md`, `indice.md` y el texto plano. |
| `web/generar_audio.py` | *Script* que genera el audio por capítulo. |

---

## Cómo leer el sitio web

La experiencia web vive en `web/index.html`. Es una SPA autocontenida
(funciona incluso abriendo el archivo directamente, sin servidor ni conexión).

### Opción A — abrir directamente

```bash
open web/index.html
```

### Opción B — servidor local (recomendado)

```bash
cd web
python3 -m http.server 8080
# abrir http://localhost:8080
```

### Características

- **Dark mode** por defecto (alternable con el botón de tema).
- Índice lateral por partes y capítulos.
- **Progreso de lectura** (barra superior + memoria de posición por capítulo).
- **Continuar leyendo** donde se quedó (persistencia en `localStorage`).
- Bloques destacados: norma, concepto, pregunta crítica, advertencia, ejemplo.
- Navegación anterior/siguiente y enlaces internos entre capítulos.
- **Reproductor de audio** por capítulo: play/pausa, retroceder/avanzar 15 s,
  barra de progreso, velocidad (0.75×–2×) y **continuidad automática** al
  siguiente capítulo.
- Diseño responsive (desktop y móvil).

---

## Cómo publicar

El sitio es 100 % estático y autocontenido. Ya está publicado en **GitHub Pages**:

- **Lectura:** <https://josoroma.github.io/anatomia-de-una-ley/>
- **Repositorio:** <https://github.com/josoroma/anatomia-de-una-ley>

El `index.html` de la raíz redirige automáticamente a `web/index.html`, por lo
que Pages funciona sin configuración adicional (rama `main`, carpeta raíz).

Como `libro.js` se carga con una etiqueta `<script>` (no con `fetch`), el libro
funciona igual por `file://` y por `http(s)://` —sin problemas de CORS.

---

## Cómo regenerar

Tras editar los capítulos, reconstruye el sitio y el manual:

```bash
python3 web/build.py
```

Para regenerar el audio (requiere red y `edge-tts`):

```bash
pip install edge-tts          # una sola vez
python3 web/generar_audio.py                 # todos
python3 web/generar_audio.py --solo 20       # un capítulo
python3 web/generar_audio.py --voz es-ES-AlvaroNeural   # otra voz
```

La voz por defecto es `es-MX-DaliaNeural` (español neutro de América Latina).

---

## Método

- **Hecho jurídico → funcionamiento institucional → incentivos y efectos →
  análisis crítico → juicio normativo.**
- Toda afirmación normativa cita su referencia (Constitución Política, Reglamento
  de la Asamblea Legislativa, jurisprudencia u obra doctrinal identificable).
- Donde la bibliografía presentó cifras en conflicto (p. ej., caducidad), la obra
  adoptó el texto vigente del RAL (art. 119, reforma de 2022) y lo indica.
- La Parte IV (anatomía crítica) es razonamiento analítico construido sobre los
  hechos jurídicos verificados; no introduce hechos empíricos adicionales.
- Las citas literales conservan el texto original.

El manual no sustituye el criterio profesional del abogado responsable.
