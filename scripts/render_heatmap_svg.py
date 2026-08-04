#!/usr/bin/env python3
"""Render the scraped contribution grid into a self-contained animated SVG.

Animation is done with native SMIL <animate> tags (no <script>, no external
CSS) since that's what GitHub actually allows to render/play inside a
markdown-embedded SVG.
"""
import json
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "contrib-heatmap.svg")

CELL = 11
GAP = 3
MARGIN_LEFT = 28
MARGIN_TOP = 36
MARGIN_RIGHT = 16
MARGIN_BOTTOM = 14

LEVEL_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG_COLOR = "#0d1117"
TEXT_COLOR = "#8b949e"
TITLE_COLOR = "#c9d1d9"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STAGGER = 0.018  # seconds between diagonally-adjacent cells
DURATION = 0.5


def month_labels(cells):
    labels = []
    seen_weeks = set()
    last_month = None
    for c in sorted(cells, key=lambda c: c["week"]):
        if c["weekday"] != 0:
            continue
        month = int(c["date"].split("-")[1])
        if month != last_month and c["week"] not in seen_weeks:
            labels.append((c["week"], MONTH_NAMES[month - 1]))
            last_month = month
            seen_weeks.add(c["week"])
    return labels


def build_svg(grid: dict) -> str:
    cells = grid["cells"]
    weeks = grid["weeks"]
    total = sum(1 for c in cells if c["level"] > 0)

    width = MARGIN_LEFT + weeks * (CELL + GAP) + MARGIN_RIGHT
    height = MARGIN_TOP + 7 * (CELL + GAP) + MARGIN_BOTTOM

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
    )
    parts.append(f'<rect width="{width}" height="{height}" rx="6" fill="{BG_COLOR}"/>')
    parts.append(
        f'<text x="{MARGIN_LEFT}" y="18" fill="{TITLE_COLOR}" font-size="13" font-weight="600">'
        f'{grid.get("username", "")} — {total} contributions in the last year</text>'
    )

    for week_idx, label in month_labels(cells):
        x = MARGIN_LEFT + week_idx * (CELL + GAP)
        parts.append(f'<text x="{x}" y="{MARGIN_TOP - 6}" fill="{TEXT_COLOR}" font-size="9">{label}</text>')

    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for wd, label in day_labels.items():
        y = MARGIN_TOP + wd * (CELL + GAP) + CELL - 2
        parts.append(f'<text x="4" y="{y}" fill="{TEXT_COLOR}" font-size="9">{label}</text>')

    for c in cells:
        x = MARGIN_LEFT + c["week"] * (CELL + GAP)
        y = MARGIN_TOP + c["weekday"] * (CELL + GAP)
        color = LEVEL_COLORS[min(c["level"], 4)]
        delay = (c["week"] + c["weekday"]) * STAGGER
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" '
            f'opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" '
            f'dur="{DURATION}s" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/>'
            f'<animate attributeName="y" from="{y + 4}" to="{y}" begin="{delay:.3f}s" '
            f'dur="{DURATION}s" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/>'
            f'</rect>'
        )

    parts.append("</svg>")
    return "".join(parts)


def main():
    with open(DATA_PATH) as f:
        grid = json.load(f)

    svg = build_svg(grid)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write(svg)

    print(f"Wrote {OUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
