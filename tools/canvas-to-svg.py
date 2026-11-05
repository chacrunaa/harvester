#!/usr/bin/env python3
"""Obsidian Canvas (.canvas) → автономный SVG.

Канвасы — рабочие схемы архитектуры, но формат Obsidian проприетарный:
ни браузер, ни GitHub их не открывают. Конвертер переносит узлы, связи
и цвета в SVG, который открывается где угодно и сам подстраивается под
светлую и тёмную тему через prefers-color-scheme.

    python3 tools/canvas-to-svg.py engine/assets/canvas/chat-engine.canvas \\
        -o ui/img/chat-engine.svg --title "Цикл одного хода агента"
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

# Палитра Obsidian Canvas. Для каждой — цвет линии и заливки отдельно
# для светлой и тёмной темы.
PALETTE = {
    "1": ("#c0392b", "#f8e3e0", "#e88b80", "#3a1f1c"),  # красный
    "2": ("#c2691d", "#fbeada", "#e5a765", "#352417"),  # оранжевый
    "3": ("#9a7d0a", "#fbf3d5", "#d8be5c", "#302a14"),  # жёлтый
    "4": ("#1f7a4d", "#e1f2e8", "#6ec89b", "#15291f"),  # зелёный
    "5": ("#1f6f8b", "#e0eff5", "#6fb6cf", "#152a33"),  # голубой
    "6": ("#6b4fb8", "#ece6fa", "#a692e0", "#241d38"),  # фиолетовый
}
DEFAULT = ("#6b6b73", "#f2f2ef", "#9b9ba4", "#232327")

PAD = 56           # поля вокруг схемы
CHAR_W = 6.65      # приблизительная ширина символа при 11.5px моноширинного
LINE_H = 15.5
FONT_SIZE = 11.5


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def visual_len(s: str) -> float:
    """Ширина строки с поправкой на широкие символы."""
    total = 0.0
    for ch in s:
        total += 1.7 if unicodedata.east_asian_width(ch) in ("W", "F") else 1.0
    return total


def clean_markdown(text: str) -> list[tuple[str, bool]]:
    """Markdown из узла → список (строка, жирная ли)."""
    out = []
    for raw in text.split("\n"):
        line = raw.rstrip()
        bold = False
        # **жирный** на всю строку
        m = re.fullmatch(r"\s*\*\*(.+?)\*\*\s*", line)
        if m:
            line, bold = m.group(1), True
        else:
            line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)        # *курсив*
        line = re.sub(r"`(.+?)`", r"\1", line)          # `код`
        line = re.sub(r"^\s*[-*]\s+", "· ", line)       # пункты списка
        line = re.sub(r"^#+\s*", "", line)              # заголовки
        out.append((line, bold))
    return out


def wrap(lines: list[tuple[str, bool]], width_px: float) -> list[tuple[str, bool]]:
    """Перенос по ширине узла."""
    limit = max(6, int((width_px - 18) / CHAR_W))
    result = []
    for text, bold in lines:
        if not text:
            result.append(("", bold))
            continue
        words, cur = text.split(" "), ""
        for w in words:
            probe = (cur + " " + w).strip()
            if visual_len(probe) <= limit or not cur:
                cur = probe
            else:
                result.append((cur, bold))
                cur = w
        if cur:
            result.append((cur, bold))
    return result


def plural(n: int, one: str, few: str, many: str) -> str:
    """Русское склонение числительного: 1 узел, 2 узла, 5 узлов."""
    rem100, rem10 = n % 100, n % 10
    if 11 <= rem100 <= 14:
        word = many
    elif rem10 == 1:
        word = one
    elif 2 <= rem10 <= 4:
        word = few
    else:
        word = many
    return f"{n} {word}"


def anchor(node: dict, side: str) -> tuple[float, float]:
    x, y, w, h = node["x"], node["y"], node["width"], node["height"]
    return {
        "top": (x + w / 2, y),
        "bottom": (x + w / 2, y + h),
        "left": (x, y + h / 2),
        "right": (x + w, y + h / 2),
    }.get(side, (x + w / 2, y + h / 2))


def control(x: float, y: float, side: str, strength: float) -> tuple[float, float]:
    return {
        "top": (x, y - strength),
        "bottom": (x, y + strength),
        "left": (x - strength, y),
        "right": (x + strength, y),
    }.get(side, (x, y))


def convert(path: Path, title: str | None) -> str:
    canvas = json.loads(path.read_text())
    nodes = {n["id"]: n for n in canvas.get("nodes", [])}
    edges = canvas.get("edges", [])
    if not nodes:
        raise SystemExit(f"{path}: в канвасе нет узлов")

    min_x = min(n["x"] for n in nodes.values())
    min_y = min(n["y"] for n in nodes.values())
    max_x = max(n["x"] + n["width"] for n in nodes.values())
    max_y = max(n["y"] + n["height"] for n in nodes.values())

    head = PAD + (34 if title else 0)
    vb_x, vb_y = min_x - PAD, min_y - head
    vb_w, vb_h = (max_x - min_x) + PAD * 2, (max_y - min_y) + head + PAD

    out: list[str] = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vb_x:.0f} {vb_y:.0f} {vb_w:.0f} {vb_h:.0f}" '
        f'width="{vb_w:.0f}" height="{vb_h:.0f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'role="img" aria-label="{esc(title or path.stem)}">'
    )

    # Автономные стили: SVG подстраивается под тему сам, даже внутри <img>.
    css = [
        ":root{--c-bg:#ffffff;--c-fg:#16161a;--c-muted:#61616b;--c-edge:#b4b4ad;--c-line:#d8d8d2;--c-fill:#f7f7f4;}",
        "@media (prefers-color-scheme: dark){:root{--c-bg:#1a1a1d;--c-fg:#ececee;--c-muted:#9b9ba4;--c-edge:#55555e;--c-line:#3a3a41;--c-fill:#232327;}}",
        ".bg{fill:var(--c-bg);}",
        ".t{fill:var(--c-fg);font-size:%.1fpx;}" % FONT_SIZE,
        ".t.b{font-weight:700;}",
        ".ttl{fill:var(--c-fg);font-size:17px;font-weight:700;}",
        ".sub{fill:var(--c-muted);font-size:11px;}",
        ".e{fill:none;stroke:var(--c-edge);stroke-width:1.7;}",
        ".elab{fill:var(--c-muted);font-size:10px;font-weight:700;}",
        ".box{stroke-width:1.6;}",
    ]
    for key, (light, lfill, dark, dfill) in PALETTE.items():
        css.append(f".s{key}{{stroke:{light};fill:{lfill};}}")
        css.append(f".x{key}{{fill:{light};}}")
    css.append(f".s0{{stroke:var(--c-line);fill:var(--c-fill);}}")
    css.append(f".x0{{fill:var(--c-muted);}}")
    dark_rules = "".join(
        f".s{k}{{stroke:{d};fill:{df};}}.x{k}{{fill:{d};}}"
        for k, (l, lf, d, df) in PALETTE.items()
    )
    css.append("@media (prefers-color-scheme: dark){%s}" % dark_rules)

    out.append("<style>" + "".join(css) + "</style>")
    out.append(
        f'<rect x="{vb_x:.0f}" y="{vb_y:.0f}" width="{vb_w:.0f}" height="{vb_h:.0f}" class="bg"/>'
    )
    out.append(
        '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="var(--c-edge)"/></marker></defs>'
    )

    if title:
        out.append(
            f'<text x="{min_x - PAD + 4:.0f}" y="{min_y - head + 30:.0f}" class="ttl">{esc(title)}</text>'
        )
        out.append(
            f'<text x="{min_x - PAD + 4:.0f}" y="{min_y - head + 48:.0f}" class="sub">'
            f'{esc(path.name)} · {plural(len(nodes), "узел", "узла", "узлов")}, '
            f'{plural(len(edges), "связь", "связи", "связей")}</text>'
        )

    # Связи — под узлами.
    for e in edges:
        a, b = nodes.get(e.get("fromNode")), nodes.get(e.get("toNode"))
        if not a or not b:
            continue
        x1, y1 = anchor(a, e.get("fromSide", "right"))
        x2, y2 = anchor(b, e.get("toSide", "left"))
        dist = max(abs(x2 - x1), abs(y2 - y1))
        s = min(150, max(32, dist * 0.42))
        cx1, cy1 = control(x1, y1, e.get("fromSide", "right"), s)
        cx2, cy2 = control(x2, y2, e.get("toSide", "left"), s)
        out.append(
            f'<path class="e" marker-end="url(#a)" '
            f'd="M{x1:.0f},{y1:.0f} C{cx1:.0f},{cy1:.0f} {cx2:.0f},{cy2:.0f} {x2:.0f},{y2:.0f}"/>'
        )
        if e.get("label"):
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            label = esc(e["label"])
            pad_w = visual_len(e["label"]) * 5.6 + 10
            out.append(
                f'<rect x="{mx - pad_w / 2:.0f}" y="{my - 9:.0f}" width="{pad_w:.0f}" '
                f'height="16" rx="8" class="bg"/>'
                f'<text x="{mx:.0f}" y="{my + 3:.0f}" class="elab" text-anchor="middle">{label}</text>'
            )

    # Узлы.
    for n in nodes.values():
        color = str(n.get("color", "")) or "0"
        if color not in PALETTE:
            color = "0"
        x, y, w, h = n["x"], n["y"], n["width"], n["height"]
        out.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'rx="8" class="box s{color}"/>'
        )

        lines = wrap(clean_markdown(n.get("text", "")), w)
        block_h = len(lines) * LINE_H
        start = y + h / 2 - block_h / 2 + LINE_H * 0.76
        for i, (line, bold) in enumerate(lines):
            if not line:
                continue
            out.append(
                f'<text x="{x + w / 2:.0f}" y="{start + i * LINE_H:.1f}" '
                f'class="t{" b" if bold else ""}" text-anchor="middle">{esc(line)}</text>'
            )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Obsidian Canvas → SVG")
    ap.add_argument("canvas", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    svg = convert(args.canvas, args.title)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg)
    print(f"{args.canvas.name} → {args.out} ({len(svg) // 1024} КБ)")


if __name__ == "__main__":
    main()
