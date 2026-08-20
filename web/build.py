#!/usr/bin/env python3
"""Build script for 'Anatomía de una Ley'.

Reads capitulos/*.md, renders them to HTML (markdown-it + custom callouts),
and produces:
  - web/data/libro.js          (window.LIBRO bundle for the SPA, works over file://)
  - web/data/plain/*.txt       (plain-text per chapter, for TTS audio)
  - indice.md                  (table of contents)
  - MANUAL-COMPLETO.md         (unified single-file book)

Usage:  python3 web/build.py
"""
import os
import re
import json
import html as html_mod
from markdown_it import MarkdownIt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = os.path.join(ROOT, "capitulos")
WEB = os.path.join(ROOT, "web")
DATA = os.path.join(WEB, "data")
PLAIN = os.path.join(DATA, "plain")

md = MarkdownIt("default", {"html": True, "typographer": True})

CALLOUT_LABELS = {
    "norma": "Norma",
    "concepto": "Concepto",
    "critica": "Pregunta crítica",
    "advertencia": "Advertencia",
    "ejemplo": "Ejemplo",
    "preguntas": "Preguntas",
}

TITULO_LIBRO = "Anatomía de una Ley"
SUBTITULO_LIBRO = "Manual crítico del procedimiento legislativo costarricense"


# --------------------------------------------------------------------------- #
# Frontmatter
# --------------------------------------------------------------------------- #
def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    meta = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        meta[key.strip()] = val
    return meta, body


# --------------------------------------------------------------------------- #
# Callouts
# --------------------------------------------------------------------------- #
def extract_callouts(text):
    """Replace '> [!tipo] ...' blocks with placeholders; return (text, placeholders)."""
    lines = text.split("\n")
    out = []
    callouts = []
    i = 0
    placeholder_re = re.compile(r"\[!([a-z]+)\]")
    while i < len(lines):
        m = placeholder_re.match(lines[i].lstrip("> ").strip())
        # A callout starts with a line whose first non-'>' content is '[!tipo]'
        stripped = lines[i].lstrip("> ").strip()
        cm = placeholder_re.match(stripped)
        if cm and lines[i].lstrip().startswith(">"):
            tipo = cm.group(1)
            # collect continuation lines
            body = []
            # first line: everything after the '[!tipo]' marker
            first = stripped[len(cm.group(0)):].strip()
            if first:
                body.append(first)
            i += 1
            while i < len(lines):
                ln = lines[i]
                if ln.lstrip().startswith(">"):
                    body.append(re.sub(r"^>\s?", "", ln))
                    i += 1
                elif ln.strip() == "" and i + 1 < len(lines) and lines[i + 1].lstrip().startswith(">"):
                    body.append("")
                    i += 1
                else:
                    break
            idx = len(callouts)
            callouts.append((tipo, "\n".join(body).strip()))
            out.append(f"<!--CALLOUT:{idx}-->")
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out), callouts


def render_callout(tipo, body_html):
    label = CALLOUT_LABELS.get(tipo, tipo.capitalize())
    icon = {
        "norma": "§",
        "concepto": "◆",
        "critica": "?",
        "advertencia": "!",
        "ejemplo": "✦",
        "preguntas": "…",
    }.get(tipo, "▸")
    return (
        f'<aside class="callout callout--{tipo}">'
        f'<div class="callout__label"><span class="callout__icon">{icon}</span>{label}</div>'
        f'<div class="callout__body">{body_html}</div>'
        f'</aside>'
    )


def render_markdown(text):
    """Render markdown with callouts."""
    text, callouts = extract_callouts(text)
    html = md.render(text)
    for idx, (tipo, body) in enumerate(callouts):
        body_html = md.render(body)
        html = html.replace(f"<!--CALLOUT:{idx}-->", render_callout(tipo, body_html))
    return html


# --------------------------------------------------------------------------- #
# Plain text (for TTS)
# --------------------------------------------------------------------------- #
def md_to_plaintext(text):
    meta, body = parse_frontmatter(text)
    body, callouts = extract_callouts(body)
    # reconstruct callouts as plain text with label prefix
    def repl(m):
        idx = int(m.group(1))
        tipo, content = callouts[idx]
        label = CALLOUT_LABELS.get(tipo, tipo)
        return f"{label}: {content}"
    body = re.sub(r"<!--CALLOUT:(\d+)-->", repl, body)
    # strip code fences (keep inner text but mark as note)
    body = re.sub(r"```[^\n]*\n(.*?)```", r"\1", body, flags=re.DOTALL)
    # headers -> plain
    body = re.sub(r"^#{1,6}\s+", "", body, flags=re.MULTILINE)
    # horizontal rules
    body = re.sub(r"^\s*---+\s*$", "", body, flags=re.MULTILINE)
    # tables -> drop the | and separator rows
    body = re.sub(r"^\s*\|?[\s:|-]+\|?\s*$", "", body, flags=re.MULTILINE)
    body = body.replace("|", " ")
    # inline markup
    body = re.sub(r"\*\*([^*]+)\*\*", r"\1", body)
    body = re.sub(r"\*([^*]+)\*", r"\1", body)
    body = re.sub(r"`([^`]+)`", r"\1", body)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    body = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", body)
    body = re.sub(r"^\s*>\s?", "", body, flags=re.MULTILINE)
    # list markers
    body = re.sub(r"^\s*[-*+]\s+", "", body, flags=re.MULTILINE)
    body = re.sub(r"^\s*\d+\.\s+", "", body, flags=re.MULTILINE)
    # collapse blank lines
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


# --------------------------------------------------------------------------- #
# Load chapters
# --------------------------------------------------------------------------- #
def load_chapters():
    files = sorted(f for f in os.listdir(CAP) if f.endswith(".md"))
    chapters = []
    for fn in files:
        with open(os.path.join(CAP, fn), encoding="utf-8") as fh:
            raw = fh.read()
        meta, body = parse_frontmatter(raw)
        num = int(meta.get("numero", 0))
        chapters.append({
            "numero": num,
            "parte": meta.get("parte", ""),
            "titulo": meta.get("titulo", fn),
            "slug": meta.get("slug", fn[:-3]),
            "resumen": meta.get("resumen", ""),
            "html": render_markdown(body),
            "plaintext": md_to_plaintext(body),
            "archivo": fn,
        })
    chapters.sort(key=lambda c: c["numero"])
    # prev/next
    for i, ch in enumerate(chapters):
        ch["prev"] = chapters[i - 1]["slug"] if i > 0 else None
        ch["next"] = chapters[i + 1]["slug"] if i < len(chapters) - 1 else None
    return chapters


# --------------------------------------------------------------------------- #
# Emit
# --------------------------------------------------------------------------- #
def build_indice(chapters):
    lines = [
        f"# {TITULO_LIBRO}",
        "",
        f"*{SUBTITULO_LIBRO}*",
        "",
        "## Índice",
        "",
    ]
    current_parte = None
    for ch in chapters:
        if ch["parte"] != current_parte:
            current_parte = ch["parte"]
            lines.append(f"\n### {current_parte}\n")
        lines.append(f"{ch['numero']:02d}. [{ch['titulo']}](capitulos/{ch['archivo']}) — {ch['resumen']}")
    lines.append("\n## Herramientas\n")
    lines.append("- [Plantilla de proyecto de ley](herramientas/plantilla-proyecto-ley.md)")
    lines.append("- [Checklist de presentación](herramientas/checklist-presentacion.md)")
    lines.append("- [Checklist de validación](herramientas/checklist-validacion.md)")
    lines.append("- [Checklist crítico](herramientas/checklist-critico.md)")
    lines.append("\n## Obra unificada\n")
    lines.append("- [Manual completo (un solo archivo)](MANUAL-COMPLETO.md)")
    lines.append("- [Sitio web del libro](web/index.html)")
    return "\n".join(lines) + "\n"


def build_manual_completo(chapters):
    lines = [
        f"# {TITULO_LIBRO}",
        "",
        f"## {SUBTITULO_LIBRO}",
        "",
        "> Obra unificada generada automáticamente desde `capitulos/`. "
        "Versión de lectura enriquecida: `web/index.html`.",
        "",
        "---",
        "",
    ]
    # TOC
    lines.append("## Índice\n")
    current_parte = None
    for ch in chapters:
        if ch["parte"] != current_parte:
            current_parte = ch["parte"]
            lines.append(f"\n### {current_parte}\n")
        lines.append(f"{ch['numero']:02d}. {ch['titulo']}\n")
    lines.append("\n---\n")
    # chapters
    for ch in chapters:
        with open(os.path.join(CAP, ch["archivo"]), encoding="utf-8") as fh:
            _, body = parse_frontmatter(fh.read())
        lines.append(f"\n\n<!-- ════ Capítulo {ch['numero']:02d} — {ch['titulo']} ════ -->\n")
        lines.append(body.strip())
        lines.append("\n")
    return "\n".join(lines) + "\n"


def build_libro_js(chapters):
    payload = {
        "titulo": TITULO_LIBRO,
        "subtitulo": SUBTITULO_LIBRO,
        "chapters": [
            {k: ch[k] for k in ("numero", "parte", "titulo", "slug", "resumen", "html", "prev", "next")}
            for ch in chapters
        ],
    }
    js = "window.LIBRO = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n"
    return js


def main():
    os.makedirs(PLAIN, exist_ok=True)
    chapters = load_chapters()
    with open(os.path.join(ROOT, "indice.md"), "w", encoding="utf-8") as fh:
        fh.write(build_indice(chapters))
    with open(os.path.join(ROOT, "MANUAL-COMPLETO.md"), "w", encoding="utf-8") as fh:
        fh.write(build_manual_completo(chapters))
    with open(os.path.join(DATA, "libro.js"), "w", encoding="utf-8") as fh:
        fh.write(build_libro_js(chapters))
    for ch in chapters:
        with open(os.path.join(PLAIN, f"{ch['numero']:02d}-{ch['slug']}.txt"), "w", encoding="utf-8") as fh:
            fh.write(ch["plaintext"] + "\n")
    print(f"OK: {len(chapters)} capítulos -> libro.js, MANUAL-COMPLETO.md, indice.md, plain/*.txt")


if __name__ == "__main__":
    main()
