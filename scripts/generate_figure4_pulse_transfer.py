from pathlib import Path
from html import escape


OUT = Path('/Users/haywoodau3/Documents/genaisubstrate/output')
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1800, 1180
BG = '#ffffff'
INK = '#17212b'
MUTED = '#52606d'
GRID = '#dbe4ec'
PANEL = '#f7fafc'
TEAL = '#008f83'
TEAL_LIGHT = '#d8f0ec'
ORANGE = '#ef8f3a'
ORANGE_LIGHT = '#fff0df'
PURPLE = '#6b5ca5'
PURPLE_LIGHT = '#ece9f7'
BLUE = '#2f6f9f'
RED = '#c84b45'


def esc(s):
    return escape(str(s), quote=True)


def tag(name, attrs='', body=''):
    return f'<{name} {attrs}>{body}</{name}>'


def text(x, y, s, size=18, fill=INK, weight='400', anchor='start', italic=False,
         family='Arial, Helvetica, sans-serif', letter=0, opacity=1.0):
    style = f'font-family:{family};font-size:{size}px;font-weight:{weight};fill:{fill};'
    if italic:
        style += 'font-style:italic;'
    if letter:
        style += f'letter-spacing:{letter}px;'
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" opacity="{opacity}" style="{style}">{esc(s)}</text>'


def rect(x, y, w, h, fill='none', stroke='none', sw=1, rx=0, dash=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>'


def line(x1, y1, x2, y2, stroke=INK, sw=1.5, dash=None, opacity=1.0):
    extra = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"{extra}/>'


def circle(cx, cy, r, fill='none', stroke='none', sw=1):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def polygon(points, fill='none', stroke='none', sw=1):
    pts = ' '.join(f'{x},{y}' for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def arrow(x1, y1, x2, y2, stroke=TEAL, sw=3, head=10):
    dx, dy = x2 - x1, y2 - y1
    mag = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / mag, dy / mag
    px, py = -uy, ux
    bx, by = x2 - ux * head, y2 - uy * head
    return line(x1, y1, bx, by, stroke, sw) + polygon(
        [(x2, y2), (bx + px * head * 0.55, by + py * head * 0.55),
         (bx - px * head * 0.55, by - py * head * 0.55)], fill=stroke)


def catalyst_icon(cx, cy, label, color, scale=1.0):
    r = 22 * scale
    out = []
    out.append(circle(cx, cy, r, fill='white', stroke=color, sw=3))
    out.append(circle(cx, cy, r * .46, fill=color, stroke='none'))
    for i in range(4):
        import math
        a = math.pi / 4 + i * math.pi / 2
        x = cx + math.cos(a) * r * .98
        y = cy + math.sin(a) * r * .98
        out.append(circle(x, y, 5 * scale, fill=color, stroke='white', sw=1.5))
    out.append(text(cx, cy + r + 25 * scale, label, size=int(16 * scale), fill=INK,
                    weight='700', anchor='middle'))
    return ''.join(out)


def panel_title(x, y, letter, title, subtitle, width):
    s = []
    s.append(text(x, y, letter, size=25, fill=TEAL, weight='700'))
    s.append(text(x + 36, y, title, size=22, fill=INK, weight='700'))
    s.append(text(x + 36, y + 27, subtitle, size=14, fill=MUTED))
    s.append(line(x, y + 45, x + width, y + 45, GRID, 1.4))
    return ''.join(s)


def xmap(v, lo, hi, x0, x1):
    return x0 + (v - lo) / (hi - lo) * (x1 - x0)


def draw_dumbbell(x0, x1, y, target, guarded, lo, hi, label, value_label=True,
                  target_color=MUTED, guarded_color=TEAL, font=14):
    xt = xmap(target, lo, hi, x0, x1)
    xg = xmap(guarded, lo, hi, x0, x1)
    left, right = sorted([xt, xg])
    out = [line(left, y, right, y, stroke=GRID, sw=5)]
    out.append(circle(xt, y, 7, fill='white', stroke=target_color, sw=2.5))
    out.append(circle(xg, y, 7, fill=guarded_color, stroke='white', sw=2))
    if value_label:
        out.append(text(xt, y - 13, f'{target:.3f}', size=font, fill=target_color,
                        anchor='middle'))
        out.append(text(xg, y + 23, f'{guarded:.3f}', size=font, fill=guarded_color,
                        anchor='middle', weight='700'))
    out.append(text(x0 - 14, y + 5, label, size=font + 1, fill=INK, anchor='end', weight='700'))
    return ''.join(out)


def axis_ticks(x0, x1, y, ticks, lo, hi, suffix='', zero=None):
    out = [line(x0, y, x1, y, stroke=INK, sw=1.2)]
    for v in ticks:
        x = xmap(v, lo, hi, x0, x1)
        out.append(line(x, y, x, y + 7, stroke=INK, sw=1.1))
        out.append(text(x, y + 25, f'{v:g}{suffix}', size=13, fill=MUTED, anchor='middle'))
    if zero is not None:
        x = xmap(zero, lo, hi, x0, x1)
        out.append(line(x, y - 10, x, y + 7, stroke=RED, sw=2))
    return ''.join(out)


def forest_row(x0, x1, y, mean, low, high, lo, hi, label, color=TEAL, value=True):
    xl = xmap(low, lo, hi, x0, x1)
    xm = xmap(mean, lo, hi, x0, x1)
    xh = xmap(high, lo, hi, x0, x1)
    out = [text(x0 - 16, y + 5, label, size=14, fill=INK, anchor='end', weight='700')]
    out.append(line(xl, y, xh, y, stroke=color, sw=4))
    out.append(line(xl, y - 8, xl, y + 8, stroke=color, sw=2))
    out.append(line(xh, y - 8, xh, y + 8, stroke=color, sw=2))
    out.append(circle(xm, y, 6.5, fill=color, stroke='white', sw=1.5))
    if value:
        out.append(text(xm, y - 12, f'{mean:+.3f}', size=12, fill=color, anchor='middle', weight='700'))
    return ''.join(out)


def build_svg():
    s = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1180" viewBox="0 0 1800 1180" role="img" aria-labelledby="title desc">',
        '<title id="title">Figure 4. PULSE-Transfer: when should information from another catalyst be borrowed?</title>',
        '<desc id="desc">A three-panel scientific figure showing fixed-replay transfer gains, robustness across 500 randomized substrate reveal routes, and scaffold-held-out transfer with an uncertain incremental pose contribution.</desc>',
        rect(0, 0, W, H, BG),
        text(42, 45, 'Figure 4', size=27, fill=TEAL, weight='700'),
        text(182, 45, 'PULSE–Transfer: when should information from another catalyst be borrowed?', size=27, fill=INK, weight='700'),
        text(42, 73, 'Progressive evidence from fixed replay to randomized routes and harder scaffold extrapolation', size=15, fill=MUTED),
    ]

    # Conceptual pre-panel schematic
    s += [rect(42, 92, 1716, 125, fill=PANEL, stroke=GRID, sw=1.2, rx=12)]
    s += [text(65, 119, 'GUARDED TRANSFER', size=12, fill=TEAL, weight='700', letter=1.2)]
    s += [text(65, 146, 'Source catalyst data', size=18, fill=INK, weight='700')]
    s += [catalyst_icon(98, 181, 'CMC-Por', PURPLE, .7)]
    s += [text(147, 187, '+', size=22, fill=MUTED, weight='700')]
    s += [text(175, 146, 'partially revealed target data', size=17, fill=INK, weight='700')]
    s += [catalyst_icon(264, 181, 'P7', ORANGE, .7)]
    s += [arrow(330, 176, 493, 176, stroke=TEAL, sw=3, head=12)]
    s += [text(411, 151, 'remove shared identities', size=13, fill=MUTED, anchor='middle'),
          text(411, 199, '13 canonical overlaps excluded', size=13, fill=RED, anchor='middle', weight='700')]
    s += [rect(520, 127, 310, 94, fill='white', stroke=TEAL, sw=1.6, rx=10)]
    s += [text(545, 153, 'target-only learner', size=16, fill=MUTED, weight='700'),
          text(545, 180, 'guarded source-assisted learner', size=16, fill=TEAL, weight='700'),
          line(545, 188, 796, 188, GRID, 1)]
    s += [arrow(853, 176, 1005, 176, stroke=TEAL, sw=3, head=12)]
    s += [rect(1034, 127, 294, 94, fill=TEAL_LIGHT, stroke=TEAL, sw=1.6, rx=10)]
    s += [text(1181, 155, 'compare target MAE', size=18, fill=INK, weight='700', anchor='middle'),
          text(1181, 184, 'as labels are revealed', size=16, fill=MUTED, anchor='middle')]
    s += [arrow(1350, 176, 1469, 176, stroke=TEAL, sw=3, head=12)]
    s += [text(1600, 151, 'stress-test the effect', size=16, fill=INK, weight='700', anchor='middle'),
          text(1600, 180, 'A fixed replay  →  B 500 routes  →  C scaffold hold-out', size=14, fill=MUTED, anchor='middle')]

    # Panels
    ax, ay, aw = 42, 247, 560
    bx, by, bw = 635, 247, 485
    cx, cy, cw = 1153, 247, 605
    s += [panel_title(ax, ay, 'A', 'Fixed replay', 'Target-only versus guarded transfer; same target reveal sequence', aw)]
    s += [panel_title(bx, by, 'B', 'Randomized-route robustness', 'Guarded − target MAE across 500 target-label reveal routes', bw)]
    s += [panel_title(cx, cy, 'C', 'Scaffold-held-out transfer', 'Harder extrapolation: transfer survives; pose-specific gain is less certain', cw)]

    # Panel A
    a0, a1 = ax + 112, ax + aw - 18
    lo, hi = 10.4, 12.7
    for tick in [10.5, 11.0, 11.5, 12.0, 12.5]:
        xt = xmap(tick, lo, hi, a0, a1)
        s.append(line(xt, 340, xt, 738, GRID, 1, opacity=.65))
        s.append(text(xt, 757, f'{tick:.1f}', size=12, fill=MUTED, anchor='middle'))
    s += [text((a0+a1)/2, 786, 'ee MAE (percentage points; lower is better)', size=13, fill=MUTED, anchor='middle')]
    s += [rect(ax + 14, 306, aw - 28, 33, fill=PURPLE_LIGHT, stroke='none', rx=6),
          catalyst_icon(ax + 42, 322, '', PURPLE, .42),
          text(ax + 67, 327, 'Fe(CMC-Por)Cl → Fe(P7)Cl', size=15, fill=INK, weight='700'),
          text(ax + aw - 24, 327, '13 shared identities excluded', size=12, fill=RED, anchor='end', weight='700')]
    s += [rect(ax + 14, 520, aw - 28, 33, fill=ORANGE_LIGHT, stroke='none', rx=6),
          catalyst_icon(ax + 42, 536, '', ORANGE, .42),
          text(ax + 67, 541, 'Fe(P7)Cl → Fe(CMC-Por)Cl', size=15, fill=INK, weight='700')]
    A1 = [('B5', 11.815, 11.654), ('P3', 11.276, 10.973), ('P4', 11.061, 10.741)]
    A2 = [('B5', 12.234, 11.702), ('P3', 12.205, 11.480), ('P4', 12.208, 11.509)]
    for y, (lab, t, g) in zip([373, 430, 487], A1):
        s.append(draw_dumbbell(a0, a1, y, t, g, lo, hi, lab))
    for y, (lab, t, g) in zip([587, 644, 701], A2):
        s.append(draw_dumbbell(a0, a1, y, t, g, lo, hi, lab))
    s += [line(ax + 16, 738, ax + aw - 16, 738, GRID, 1.2),
          circle(ax + 31, 811, 7, fill='white', stroke=MUTED, sw=2), text(ax + 47, 817, 'Target only', size=13, fill=MUTED),
          circle(ax + 158, 811, 7, fill=TEAL, stroke='white', sw=1.5), text(ax + 174, 817, 'Guarded transfer', size=13, fill=TEAL, weight='700'),
          text(ax + aw - 18, 817, 'Directional evidence, not transfer acceptance', size=13, fill=RED, anchor='end', weight='700')]

    # Panel B
    b0, b1 = bx + 145, bx + bw - 18
    blo, bhi = -0.60, 0.10
    for tick in [-0.6, -0.4, -0.2, 0.0]:
        xt = xmap(tick, blo, bhi, b0, b1)
        s.append(line(xt, 338, xt, 737, RED if tick == 0 else GRID, 2 if tick == 0 else 1, opacity=.75))
        s.append(text(xt, 758, f'{tick:+.1f}', size=12, fill=RED if tick == 0 else MUTED, anchor='middle', weight='700' if tick == 0 else '400'))
    s += [text((b0+b1)/2, 786, 'Guarded − target MAE', size=13, fill=MUTED, anchor='middle'),
          text(b0 + 12, 323, '← guarded transfer better', size=13, fill=TEAL, weight='700')]
    rowsB = [
        ('CMC→P7', 'B5', -0.230, -0.254, -0.205),
        ('', 'P3', -0.311, -0.345, -0.279),
        ('', 'P4', -0.417, -0.451, -0.382),
        ('P7→CMC', 'B5', -0.399, -0.443, -0.356),
        ('', 'P3', -0.460, -0.499, -0.421),
        ('', 'P4', -0.501, -0.533, -0.466),
    ]
    ys = [381, 431, 481, 588, 638, 688]
    for y, (direction, lab, mean, low, high) in zip(ys, rowsB):
        if direction:
            fill = PURPLE_LIGHT if direction == 'CMC→P7' else ORANGE_LIGHT
            s.append(rect(bx + 14, y - 27, bw - 28, 30, fill=fill, stroke='none', rx=5))
        s.append(forest_row(b0, b1, y, mean, low, high, blo, bhi, f'{direction + "  " if direction else "      "}{lab}', color=TEAL))
        s.append(text(b1 + 8, y + 5, f'{mean:+.3f}', size=12, fill=TEAL, weight='700'))
    s += [text(bx + 14, 742, '500 randomized routes; error bars are 95% bootstrap intervals', size=12, fill=MUTED),
          text(bx + 14, 810, 'All shown intervals remain below zero.', size=14, fill=TEAL, weight='700'),
          text(bx + 14, 834, 'Ordering perturbation does not reverse the directional benefit.', size=13, fill=INK)]

    # Panel C1
    c0, c1 = cx + 170, cx + cw - 18
    clo, chi = 9.5, 25.5
    for tick in [10, 15, 20, 25]:
        xt = xmap(tick, clo, chi, c0, c1)
        s.append(line(xt, 374, xt, 570, GRID, 1, opacity=.7))
        s.append(text(xt, 590, f'{tick}', size=12, fill=MUTED, anchor='middle'))
    s += [text((c0+c1)/2, 615, 'Scaffold-held-out ee MAE', size=13, fill=MUTED, anchor='middle'),
          rect(cx + 14, 332, cw - 28, 29, fill=ORANGE_LIGHT, stroke='none', rx=5),
          text(cx + 28, 352, 'C1  Transfer itself under scaffold exclusion', size=15, fill=INK, weight='700')]
    C1 = [('P7→CMC', 24.103, 18.382), ('CMC→P7', 14.816, 10.643)]
    for y, (lab, t, g) in zip([423, 520], C1):
        s.append(draw_dumbbell(c0, c1, y, t, g, clo, chi, lab, font=13))
    s += [circle(cx + 27, 664, 7, fill='white', stroke=MUTED, sw=2), text(cx + 42, 669, 'Target only', size=12, fill=MUTED),
          circle(cx + 135, 664, 7, fill=TEAL, stroke='white', sw=1.5), text(cx + 150, 669, 'Guarded', size=12, fill=TEAL, weight='700'),
          text(cx + cw - 18, 669, '12/22 scaffold groups; different validation protocol from A', size=11, fill=MUTED, anchor='end')]

    # Panel C2
    s += [rect(cx + 14, 700, cw - 28, 29, fill=PURPLE_LIGHT, stroke='none', rx=5),
          text(cx + 28, 720, 'C2  Incremental pose effect during transfer', size=15, fill=INK, weight='700')]
    d0, d1 = cx + 175, cx + cw - 18
    dlo, dhi = -4.6, 2.4
    for tick in [-4, -2, 0, 2]:
        xt = xmap(tick, dlo, dhi, d0, d1)
        s.append(line(xt, 773, xt, 924, RED if tick == 0 else GRID, 2 if tick == 0 else 1, opacity=.8))
        s.append(text(xt, 944, f'{tick:+.0f}', size=12, fill=RED if tick == 0 else MUTED, anchor='middle', weight='700' if tick == 0 else '400'))
    s += [text(d0 + 12, 758, 'negative favors pose', size=12, fill=PURPLE, weight='700'),
          text((d0+d1)/2, 968, 'Incremental P3 guarded MAE − B5 guarded MAE', size=12, fill=MUTED, anchor='middle')]
    s.append(forest_row(d0, d1, 825, 0.666, -0.589, 1.856, dlo, dhi, 'CMC→P7', color=PURPLE, value=True))
    s.append(forest_row(d0, d1, 890, -1.826, -3.968, 0.272, dlo, dhi, 'P7→CMC', color=PURPLE, value=True))
    s += [text(cx + 14, 1018, 'Both scaffold-level pose intervals include zero.', size=14, fill=RED, weight='700'),
          text(cx + 14, 1043, 'Transfer survives harder extrapolation; pose-specific gain is less certain.', size=13, fill=INK)]

    # Global footer
    s += [line(42, 1080, 1758, 1080, GRID, 1.2),
          text(42, 1107, 'Interpretation: A establishes a directional signal; B shows route robustness; C separates transfer benefit from a less-certain incremental pose benefit.', size=13, fill=INK),
          text(1758, 1107, 'MAE in ee percentage points; lower is better.', size=12, fill=MUTED, anchor='end'),
          '</svg>']
    return ''.join(s)


def crop_svg(full_svg, x, y, w, h, panel_label):
    """Create a standalone crop while retaining the original vector artwork."""
    body = full_svg.split('>', 1)[1].rsplit('</svg>', 1)[0]
    return ''.join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
        f'<title id="title">Figure 4{panel_label}</title>',
        f'<desc id="desc">Standalone panel {panel_label} from Figure 4, PULSE-Transfer.</desc>',
        f'<g transform="translate({-x},{-y})">', body, '</g>', '</svg>'
    ])


if __name__ == '__main__':
    full = build_svg()
    path = OUT / 'figure4_pulse_transfer.svg'
    path.write_text(full, encoding='utf-8')

    crops = {
        'figure4A_fixed_replay.svg': (20, 225, 600, 620, 'A'),
        'figure4B_randomized_routes.svg': (615, 225, 525, 635, 'B'),
        'figure4C_scaffold_held_out.svg': (1135, 225, 645, 850, 'C'),
    }
    for name, (x, y, w, h, label) in crops.items():
        (OUT / 'figure4' / name).write_text(crop_svg(full, x, y, w, h, label), encoding='utf-8')
        print(OUT / 'figure4' / name)
    print(path)
