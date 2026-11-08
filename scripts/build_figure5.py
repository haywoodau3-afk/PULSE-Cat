from __future__ import annotations

import csv
import html
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 2600, 1800
INK = "#24313A"
MUTED = "#5D6A72"
GRID = "#DCE3E7"
PANEL = "#FFFFFF"
BG = "#F6F8F9"
GEN = "#C45B35"
ENUM = "#087F8C"
GEN_LIGHT = "#F3DDD5"
ENUM_LIGHT = "#D9EEF0"
GOLD = "#C38B2F"
GREEN = "#3E8A6E"


def esc(v: object) -> str:
    return html.escape(str(v), quote=True)


def t(x, y, s, size=22, fill=INK, weight="400", anchor="start", family="Arial"):
    return f'<text x="{x}" y="{y}" font-family="{family}, sans-serif" font-size="{size}px" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>'


def line(x1, y1, x2, y2, stroke=GRID, sw=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def rect(x, y, w, h, fill="none", stroke="none", sw=1, r=0, opacity=1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'


def poly(points, fill, stroke="none", sw=1, opacity=1):
    pts = " ".join(f"{x},{y}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'


def path(d, fill="none", stroke="none", sw=1, opacity=1):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'


def panel(x, y, w, h, letter, title, subtitle):
    s = rect(x, y, w, h, PANEL, "#D7E0E4", 2, 18)
    s += rect(x, y, 12, h, ENUM, "none", 0, 6)
    s += t(x + 32, y + 48, letter, 30, ENUM, "700")
    s += t(x + 78, y + 48, title, 28, INK, "700")
    s += t(x + 78, y + 82, subtitle, 17, MUTED)
    return s


def width_for(n, maxw=610):
    # A gentle power transform preserves visibility of late-stage funnel blocks
    # while retaining the strong scale contrast between the two routes.
    return max(56, 36 + maxw * (n / 50560) ** 0.62)


def funnel(x, y, w, h, title, color, light, values, labels, note=None):
    s = t(x + w / 2, y, title, 23, color, "700", "middle")
    s += t(x + w / 2, y + 30, "same nominal input budget", 14, MUTED, "400", "middle")
    top = y + 65
    step = h / len(values)
    for i, (value, label) in enumerate(zip(values, labels)):
        ww = width_for(value, w - 20)
        yy = top + i * step + 6
        xx = x + (w - ww) / 2
        hh = step - 14
        fill = light if i < len(values) - 1 else color
        text_fill = color if i < len(values) - 1 else "#FFFFFF"
        s += poly([(xx + 14, yy), (xx + ww - 14, yy), (xx + ww, yy + hh / 2),
                   (xx + ww - 14, yy + hh), (xx + 14, yy + hh),
                   (xx, yy + hh / 2)], fill, color, 2)
        s += t(x + w / 2, yy + hh / 2 - 4, f"{value:,}", 25, text_fill, "700", "middle")
        s += t(x + w / 2, yy + hh / 2 + 19, label, 13, text_fill, "400", "middle")
        if i < len(values) - 1:
            s += line(x + w / 2, yy + hh + 2, x + w / 2, yy + step - 3, color, 2)
            s += t(x + w / 2 + ww / 2 + 12, yy + hh / 2 + 5, "↓", 19, color, "700")
    if note:
        s += rect(x + 24, y + h + 14, w - 48, 66, "#FFF7E6", "#E7C77C", 1.5, 10)
        s += t(x + 38, y + h + 38, "Enumeration provenance note", 13, GOLD, "700")
        s += t(x + 38, y + h + 58, note, 13, MUTED)
    return s


def axis(x, y, w, h, xmin, xmax, ticks, xlabel, ylabel):
    s = line(x, y + h, x + w, y + h, MUTED, 1.5)
    s += line(x, y, x, y + h, MUTED, 1.5)
    for tick in ticks:
        tx = x + (tick - xmin) / (xmax - xmin) * w
        s += line(tx, y + h, tx, y + h + 7, MUTED, 1.2)
        s += t(tx, y + h + 27, f"{tick:g}", 13, MUTED, "400", "middle")
    s += t(x + w / 2, y + h + 53, xlabel, 15, MUTED, "400", "middle")
    if ylabel:
        s += t(x - 42, y + h / 2, ylabel, 15, MUTED, "400", "middle")
    return s


def similarity_silhouette(x, y, w, h, mean, color, label, lower=False):
    # Deliberately qualitative: the supplied specification reports means, not the
    # underlying 500-point diagnostics. These silhouettes communicate direction
    # without pretending to reproduce unavailable observations.
    mu = x + (mean / 0.8) * w
    spread = w * (0.16 if lower else 0.13)
    pts_top, pts_bottom = [], []
    for i in range(41):
        xx = x + i * w / 40
        z = (xx - mu) / spread
        yy = y + h / 2 - (h * 0.43) * math.exp(-0.5 * z * z)
        pts_top.append((xx, yy))
        pts_bottom.append((xx, y + h - (yy - y)))
    s = path("M " + " L ".join(f"{a},{b}" for a, b in pts_top + list(reversed(pts_bottom))) + " Z", color, color, 1.5, 0.45)
    s += line(mu, y + 6, mu, y + h - 6, color, 2, "6 5")
    s += t(x, y - 8, label, 15, color, "700")
    s += t(mu + 8, y + h / 2 - 4, f"mean {mean:.3f}", 14, color, "700")
    return s


def load_predictions():
    vals = {}
    for name, file in [("Generated", ROOT / "data/expansion/pptl/funnel-production-ee.csv"),
                       ("Enumerated", ROOT / "data/expansion/pptl/funnel-enumeration-ee.csv")]:
        with file.open(newline="") as fh:
            rows = csv.DictReader(fh)
            vals[name] = [float(r["ee_prediction_development"]) for r in rows
                          if r["contract_valid"] == "true" and r["ad_status"] == "in_domain"]
    return vals


def density_path(vals, x, y, w, h, xmin=35, xmax=100, bins=36, color=GEN):
    counts = [0] * bins
    for v in vals:
        idx = min(bins - 1, max(0, int((v - xmin) / (xmax - xmin) * bins)))
        counts[idx] += 1
    smooth = []
    for i in range(bins):
        smooth.append(sum(counts[max(0, i - 1):min(bins, i + 2)]) / 3)
    peak = max(smooth) or 1
    pts = []
    for i, c in enumerate(smooth):
        xx = x + (i + 0.5) / bins * w
        yy = y + h - (c / peak) * h * 0.82
        pts.append((xx, yy))
    d = f"M {x},{y+h} L " + " L ".join(f"{px},{py}" for px, py in pts) + f" L {x+w},{y+h} Z"
    return path(d, color, color, 2, 0.28) + path("M " + " L ".join(f"{px},{py}" for px, py in pts), "none", color, 3)


def structure_card(x, y, w, h, row, color):
    cid = row["candidate_id"]
    ee = float(row["predicted_ee"])
    smi = row["canonical_smiles"]
    s = rect(x, y, w, h, "#FBFCFD", "#D6E0E4", 1.5, 12)
    s += t(x + 14, y + 25, cid, 13, color, "700")
    s += t(x + w - 14, y + 25, f"{ee:.1f}%", 15, color, "700", "end")
    # Shared aryl-azide / two-carbon tether motif with explicit substituent labels.
    cy = y + 72
    r = 31
    left = x + 64
    right = x + 178
    def hexagon(cx, cy, rr):
        pts = [(cx + rr * math.cos(math.radians(30 + i * 60)), cy + rr * math.sin(math.radians(30 + i * 60))) for i in range(6)]
        return line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], INK, 2) + \
               line(pts[1][0], pts[1][1], pts[2][0], pts[2][1], INK, 2) + \
               line(pts[2][0], pts[2][1], pts[3][0], pts[3][1], INK, 2) + \
               line(pts[3][0], pts[3][1], pts[4][0], pts[4][1], INK, 2) + \
               line(pts[4][0], pts[4][1], pts[5][0], pts[5][1], INK, 2) + \
               line(pts[5][0], pts[5][1], pts[0][0], pts[0][1], INK, 2)
    s += hexagon(left, cy, r) + hexagon(right, cy, r)
    s += line(left + r * 0.87, cy + r * 0.5, right - r * 0.87, cy + r * 0.5, INK, 2)
    s += line(left - r * 0.87, cy - r * 0.5, left - 52, cy - 30, INK, 2)
    s += t(left - 57, cy - 36, "N₃", 14, "#7C3B75", "700", "end")
    # map record-specific functional groups from the sealed SMILES
    labels = []
    if "C(=O)OC" in smi:
        labels.append("CO₂Me")
    if "C(=O)OCC" in smi:
        labels.append("OCO₂")
    if "C(=O)O" in smi and "C(=O)OC" not in smi and "C(=O)OCC" not in smi:
        labels.append("CO₂H")
    if "CNC(=O)O" in smi:
        labels.append("NHCO₂")
    if "C(=O)N" in smi:
        labels.append("CONMe₂")
    if "O" in smi and not labels:
        labels.append("OH")
    if "CCO" in smi:
        labels.append("CH₂CH₂OH")
    if "C(F)(F)F" in smi:
        labels.append("CF₃")
    if "Cl" in smi:
        labels.append("Cl")
    if "ccn" in smi or "ncc" in smi:
        labels.append("pyridyl")
    if "ccoc" in smi:
        labels.append("furan")
    if "ccsc" in smi:
        labels.append("thiophene")
    if not labels:
        labels.append("H")
    # Keep labels compact and traceable without overcrowding the card.
    if len(labels) > 2:
        labels = labels[:2] + ["+"]
    s += t(right, cy - 45, " · ".join(labels), 12, MUTED, "700", "middle")
    s += t(x + 14, y + h - 14, smi[:42] + ("…" if len(smi) > 42 else ""), 10, MUTED)
    return s


def panel_a(x, y, w, h):
    s = panel(x, y, w, h, "A", "Candidate-generation and screening funnels",
              "Different search strategies produce very different usable candidate pools")
    labels = ["raw molecular strings", "unique canonical", "structurally eligible", "in applicability domain", "frozen scored"]
    s += funnel(x + 35, y + 125, 510, 570, "Constrained recurrent generation", GEN, GEN_LIGHT,
                [50560, 9184, 563, 483, 483], labels)
    s += funnel(x + 660, y + 125, 510, 570, "Deterministic enumeration", ENUM, ENUM_LIGHT,
                [50560, 25955, 18545, 18350, 18223], labels,
                "18,350 in-domain → 18,223 scored; 127 eligible candidates lack prediction rows")
    s += rect(x + 35, y + 738, w - 70, 47, "#F1F5F6", "none", 0, 9)
    s += t(x + 52, y + 768, "Validity", 15, INK, "700") + t(x + 132, y + 768, "chemical constraints", 15, MUTED)
    s += t(x + 415, y + 768, "Applicability", 15, INK, "700") + t(x + 540, y + 768, "supported by learned domain", 15, MUTED)
    s += t(x + 900, y + 768, "Scorability", 15, INK, "700") + t(x + 1013, y + 768, "frozen prediction available", 15, MUTED)
    return s


def panel_b(x, y, w, h):
    s = panel(x, y, w, h, "B", "Chemical-space behavior",
              "Generation increases internal diversity without simply leaving known chemical space")
    s += rect(x + 35, y + 115, w - 70, 56, "#F8F1E5", "#E7D3A9", 1.5, 10)
    s += t(x + w / 2, y + 140, "More internally diverse", 19, GOLD, "700", "middle")
    s += t(x + w / 2, y + 161, "≠ farther from known chemistry", 19, GOLD, "700", "middle")
    bx, by, bw, bh = x + 82, y + 235, 480, 350
    s += t(bx, by - 52, "B1  Internal pairwise Tanimoto similarity", 18, INK, "700")
    s += axis(bx, by, bw, bh, 0, .8, [0, .2, .4, .6, .8], "pairwise similarity", "")
    s += similarity_silhouette(bx, by + 52, bw, 90, .312, GEN, "Generated")
    s += similarity_silhouette(bx, by + 190, bw, 90, .412, ENUM, "Enumerated")
    s += t(bx + bw, by + bh + 86, "lower mean = greater internal diversity", 13, MUTED, "400", "end")
    bx2 = x + 682
    s += t(bx2, by - 52, "B2  Maximum similarity to reference set", 18, INK, "700")
    s += axis(bx2, by, bw, bh, 0, .8, [0, .2, .4, .6, .8], "maximum reference similarity", "")
    s += similarity_silhouette(bx2, by + 52, bw, 90, .487, GEN, "Generated")
    s += similarity_silhouette(bx2, by + 190, bw, 90, .457, ENUM, "Enumerated")
    s += t(bx2 + bw, by + bh + 86, "means from matched 500-candidate diagnostics", 13, MUTED, "400", "end")
    s += rect(x + 35, y + 700, w - 70, 65, "#F1F5F6", "none", 0, 9)
    s += t(x + 54, y + 727, "Reported means", 14, INK, "700")
    s += t(x + 188, y + 727, "pairwise: 0.312 vs 0.412", 14, GEN, "700")
    s += t(x + 492, y + 727, "reference maximum: 0.487 vs 0.457", 14, ENUM, "700")
    s += t(x + 54, y + 750, "Silhouette shapes are schematic because raw 500-point distributions were not supplied in the specification.", 12, MUTED)
    return s


def panel_c(x, y, w, h, pred):
    s = panel(x, y, w, h, "C", "Frozen predicted-ee distributions",
              "The frozen Morgan–Ridge model favors a higher-ee region of the enumerated pool")
    px, py, pw, ph = x + 95, y + 175, 980, 460
    s += axis(px, py, pw, ph, 35, 100, [40, 50, 60, 70, 80, 90, 100], "predicted ee (%)", "normalized density")
    s += density_path(pred["Generated"], px, py + 10, pw, ph - 10, color=GEN)
    s += density_path(pred["Enumerated"], px, py + 10, pw, ph - 10, color=ENUM)
    for value, color, label in [(56.017, GEN, "Generated  n=483"), (75.305, ENUM, "Enumerated  n=18,223")]:
        xx = px + (value - 35) / 65 * pw
        s += line(xx, py + 15, xx, py + ph, color, 2, "7 6")
        s += t(xx + 7, py + 32, f"mean {value:.3f}%", 14, color, "700")
        s += rect(x + 1080, py + (0 if color == GEN else 70), 145, 54, color, "none", 0, 9)
        s += t(x + 1092, py + (0 if color == GEN else 70) + 21, label, 14, "#FFFFFF", "700")
        top = 69.411 if color == GEN else 85.806
        s += t(x + 1092, py + (0 if color == GEN else 70) + 42, f"top-10 mean {top:.3f}%", 12, "#FFFFFF")
    s += rect(x + 95, y + 690, 1130, 90, "#FFF7E6", "#E7C77C", 1.5, 10)
    s += t(x + 115, y + 718, "Prediction-only prioritization", 15, GOLD, "700")
    s += t(x + 115, y + 744, "These are frozen-model rankings, not experimental outcomes; 127 eligible enumeration candidates lacking rows are excluded.", 14, MUTED)
    s += t(x + 115, y + 766, "Experimental testing is required before either route can be linked to successful scope expansion.", 14, MUTED)
    return s


def load_sealed():
    file = ROOT / "data/expansion/pptl/sealed-prospective-panel.csv"
    with file.open(newline="") as fh:
        return list(csv.DictReader(fh))


def panel_d(x, y, w, h, sealed):
    s = panel(x, y, w, h, "D", "Sealed prospective proposal panel",
              "Virtual exploration ends in a fixed, experimentally testable proposal")
    # Seal
    s += rect(x + 910, y + 22, 255, 46, "#FFF4E2", "#D7A94D", 2, 22)
    s += t(x + 1037, y + 51, "🔒  SEALED  ·  no outcomes used", 14, GOLD, "700", "middle")
    s += t(x + 35, y + 123, "16 proposed substrates", 21, INK, "700")
    s += t(x + 35, y + 150, "8 PULSE-Cat branch  +  8 comparator branch", 15, MUTED)
    grid_x, grid_y = x + 34, y + 177
    col_w, row_h = 560, 260
    # matrix headers
    s += rect(grid_x, grid_y, col_w, 45, ENUM_LIGHT, "none", 0, 8)
    s += rect(grid_x + col_w + 18, grid_y, col_w, 45, GEN_LIGHT, "none", 0, 8)
    s += t(grid_x + col_w / 2, grid_y + 29, "PULSE-Cat branch", 18, ENUM, "700", "middle")
    s += t(grid_x + col_w + 18 + col_w / 2, grid_y + 29, "Comparator branch", 18, GEN, "700", "middle")
    for rname, rletter, yy in [("Proposed Round 1", "A", grid_y + 62), ("Proposed Round 2", "B", grid_y + 321)]:
        s += t(grid_x, yy + 62, rname, 15, MUTED, "700")
        rows = [q for q in sealed if q["round"] == rletter]
        cop = [q for q in rows if q["branch"] == "copilot"]
        cmp = [q for q in rows if q["branch"] == "comparator"]
        for j, q in enumerate(cop):
            s += structure_card(grid_x + 132 + (j % 2) * 208, yy + (j // 2) * 100, 194, 92, q, ENUM)
        for j, q in enumerate(cmp):
            s += structure_card(grid_x + col_w + 18 + 132 + (j % 2) * 208, yy + (j // 2) * 100, 194, 92, q, GEN)
    s += rect(x + 35, y + 708, w - 70, 52, "#F1F5F6", "none", 0, 9)
    s += t(x + 55, y + 730, "Fixed before outcomes are known", 13, INK, "700")
    s += t(x + 55, y + 749, "Distinct from the 16-member morphology-balanced development shortlist", 12, MUTED)
    s += t(x + w - 55, y + 730, "IDs + scores from sealed-prospective-panel.csv", 11, MUTED, "400", "end")
    s += t(x + w - 55, y + 749, "PULSE-Cat = copilot branch in the persisted record", 11, MUTED, "400", "end")
    return s


def build_full():
    pred = load_predictions()
    sealed = load_sealed()
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
    s += f'<title>Figure 5 — PULSE-Explore: from learned substrate space to prospective candidate proposals</title>'
    s += rect(0, 0, W, H, BG)
    s += t(62, 70, "Figure 5", 38, INK, "700")
    s += t(235, 70, "PULSE-Explore: from learned substrate space to prospective candidate proposals", 31, INK, "400")
    s += t(62, 106, "CREATE  →  CHARACTERIZE  →  PRIORITIZE  →  PROPOSE", 16, ENUM, "700")
    s += panel_a(50, 135, 1250, 815)
    s += panel_b(1300, 135, 1250, 815)
    s += panel_c(50, 985, 1250, 760, pred)
    s += panel_d(1300, 985, 1250, 760, sealed)
    s += t(62, 1780, "All ee values in Panels C–D are computational predictions; candidate IDs and structures are drawn from the sealed workspace record.", 13, MUTED)
    s += "</svg>"
    (OUT / "figure5_pulse_explore.svg").write_text(s)
    def standalone(name, width, height, body):
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
        svg += rect(0, 0, width, height, BG)
        svg += body
        svg += "</svg>"
        (OUT / name).write_text(svg)
    standalone("figure5a_candidate_funnels.svg", 1250, 815, panel_a(0, 0, 1250, 815))
    standalone("figure5b_chemical_space.svg", 1250, 815, panel_b(0, 0, 1250, 815))
    standalone("figure5c_predicted_ee.svg", 1250, 760, panel_c(0, 0, 1250, 760, pred))
    standalone("figure5d_sealed_panel.svg", 1250, 760, panel_d(0, 0, 1250, 760, sealed))
    return OUT / "figure5_pulse_explore.svg"


if __name__ == "__main__":
    p = build_full()
    print(p)
