from pathlib import Path

from generate_figure4_pulse_transfer import (
    BG,
    GRID,
    INK,
    MUTED,
    ORANGE,
    ORANGE_LIGHT,
    PURPLE,
    PURPLE_LIGHT,
    RED,
    TEAL,
    catalyst_icon,
    circle,
    draw_dumbbell,
    forest_row,
    line,
    panel_title,
    rect,
    text,
    xmap,
)


OUT = Path('/Users/haywoodau3/Documents/genaisubstrate/output/figure4')


def svg_document(width, height, panel, body):
    return ''.join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">Figure 4{panel}</title>',
        f'<desc id="desc">Independently plotted editable vector panel {panel} from Figure 4, PULSE-Transfer.</desc>',
        rect(0, 0, width, height, BG),
        body,
        '</svg>',
    ])


def panel_a():
    width, height = 720, 790
    ax, ay, aw = 32, 52, 656
    a0, a1 = ax + 132, ax + aw - 18
    lo, hi = 10.4, 12.7
    s = [panel_title(ax, ay, 'A', 'Fixed replay', 'Target-only versus guarded transfer; same target reveal sequence', aw)]
    for tick in [10.5, 11.0, 11.5, 12.0, 12.5]:
        xt = xmap(tick, lo, hi, a0, a1)
        s += [line(xt, 145, xt, 565, GRID, 1, opacity=.65),
              text(xt, 587, f'{tick:.1f}', size=13, fill=MUTED, anchor='middle')]
    s += [text((a0 + a1) / 2, 615, 'ee MAE (percentage points; lower is better)', size=14, fill=MUTED, anchor='middle')]
    s += [rect(ax + 16, 108, aw - 32, 36, fill=PURPLE_LIGHT, stroke='none', rx=6),
          catalyst_icon(ax + 45, 126, '', PURPLE, .42),
          text(ax + 72, 131, 'Fe(CMC-Por)Cl → Fe(P7)Cl', size=16, fill=INK, weight='700'),
          text(ax + aw - 26, 131, '13 shared identities excluded', size=12, fill=RED, anchor='end', weight='700'),
          rect(ax + 16, 335, aw - 32, 36, fill=ORANGE_LIGHT, stroke='none', rx=6),
          catalyst_icon(ax + 45, 353, '', ORANGE, .42),
          text(ax + 72, 358, 'Fe(P7)Cl → Fe(CMC-Por)Cl', size=16, fill=INK, weight='700')]
    a1_data = [('B5', 11.815, 11.654), ('P3', 11.276, 10.973), ('P4', 11.061, 10.741)]
    a2_data = [('B5', 12.234, 11.702), ('P3', 12.205, 11.480), ('P4', 12.208, 11.509)]
    for y, row in zip([180, 237, 294], a1_data):
        s.append(draw_dumbbell(a0, a1, y, row[1], row[2], lo, hi, row[0], font=14))
    for y, row in zip([409, 466, 523], a2_data):
        s.append(draw_dumbbell(a0, a1, y, row[1], row[2], lo, hi, row[0], font=14))
    s += [line(ax + 16, 565, ax + aw - 16, 565, GRID, 1.2),
          circle(ax + 34, 660, 7, fill='white', stroke=MUTED, sw=2),
          text(ax + 51, 666, 'Target only', size=13, fill=MUTED),
          circle(ax + 171, 660, 7, fill=TEAL, stroke='white', sw=1.5),
          text(ax + 188, 666, 'Guarded transfer', size=13, fill=TEAL, weight='700'),
          text(ax + aw - 20, 666, 'Directional evidence, not transfer acceptance', size=13, fill=RED, anchor='end', weight='700')]
    return svg_document(width, height, 'A', ''.join(s))


def panel_b():
    width, height = 680, 760
    bx, by, bw = 30, 52, 620
    b0, b1 = bx + 180, bx + bw - 20
    blo, bhi = -0.60, 0.10
    s = [panel_title(bx, by, 'B', 'Randomized-route robustness', 'Guarded − target MAE across 500 target-label reveal routes', bw)]
    for tick in [-0.6, -0.4, -0.2, 0.0]:
        xt = xmap(tick, blo, bhi, b0, b1)
        s += [line(xt, 145, xt, 542, RED if tick == 0 else GRID, 2 if tick == 0 else 1, opacity=.75),
              text(xt, 565, f'{tick:+.1f}', size=13, fill=RED if tick == 0 else MUTED, anchor='middle', weight='700' if tick == 0 else '400')]
    s += [text((b0 + b1) / 2, 594, 'Guarded − target MAE', size=14, fill=MUTED, anchor='middle'),
          text(b0 + 8, 130, '← guarded transfer better', size=13, fill=TEAL, weight='700')]
    rows = [
        ('B5', -0.230, -0.254, -0.205),
        ('P3', -0.311, -0.345, -0.279),
        ('P4', -0.417, -0.451, -0.382),
        ('B5', -0.399, -0.443, -0.356),
        ('P3', -0.460, -0.499, -0.421),
        ('P4', -0.501, -0.533, -0.466),
    ]
    s += [rect(bx + 16, 154, bw - 32, 30, fill=PURPLE_LIGHT, stroke='none', rx=5),
          text(bx + 30, 174, 'CMC→P7', size=14, fill=INK, weight='700'),
          rect(bx + 16, 364, bw - 32, 30, fill=ORANGE_LIGHT, stroke='none', rx=5),
          text(bx + 30, 384, 'P7→CMC', size=14, fill=INK, weight='700')]
    ys = [215, 265, 315, 425, 475, 525]
    for y, (lab, mean, low, high) in zip(ys, rows):
        s += [forest_row(b0, b1, y, mean, low, high, blo, bhi, lab, color=TEAL),
              text(b1 + 8, y + 5, f'{mean:+.3f}', size=12, fill=TEAL, weight='700')]
    s += [text(bx + 16, 620, '500 randomized routes; error bars are 95% bootstrap intervals', size=12, fill=MUTED),
          text(bx + 16, 690, 'All shown intervals remain below zero.', size=14, fill=TEAL, weight='700'),
          text(bx + 16, 716, 'Ordering perturbation does not reverse the directional benefit.', size=13, fill=INK)]
    return svg_document(width, height, 'B', ''.join(s))


def panel_c():
    width, height = 780, 920
    cx, cy, cw = 30, 52, 720
    c0, c1 = cx + 210, cx + cw - 20
    clo, chi = 9.5, 25.5
    s = [panel_title(cx, cy, 'C', 'Scaffold-held-out transfer', 'Harder extrapolation: transfer survives; pose-specific gain is less certain', cw),
         rect(cx + 16, 108, cw - 32, 32, fill=ORANGE_LIGHT, stroke='none', rx=5),
         text(cx + 30, 130, 'C1  Transfer itself under scaffold exclusion', size=16, fill=INK, weight='700')]
    for tick in [10, 15, 20, 25]:
        xt = xmap(tick, clo, chi, c0, c1)
        s += [line(xt, 165, xt, 360, GRID, 1, opacity=.7),
              text(xt, 382, f'{tick}', size=13, fill=MUTED, anchor='middle')]
    s += [text((c0 + c1) / 2, 410, 'Scaffold-held-out ee MAE', size=14, fill=MUTED, anchor='middle')]
    for y, row in zip([220, 315], [('P7→CMC', 24.103, 18.382), ('CMC→P7', 14.816, 10.643)]):
        s.append(draw_dumbbell(c0, c1, y, row[1], row[2], clo, chi, row[0], font=14))
    s += [circle(cx + 34, 458, 7, fill='white', stroke=MUTED, sw=2),
          text(cx + 51, 463, 'Target only', size=13, fill=MUTED),
          circle(cx + 171, 458, 7, fill=TEAL, stroke='white', sw=1.5),
          text(cx + 188, 463, 'Guarded', size=13, fill=TEAL, weight='700'),
          text(cx + cw - 20, 463, '12/22 scaffold groups; different validation protocol from A', size=12, fill=MUTED, anchor='end'),
          rect(cx + 16, 505, cw - 32, 32, fill=PURPLE_LIGHT, stroke='none', rx=5),
          text(cx + 30, 527, 'C2  Incremental pose effect during transfer', size=16, fill=INK, weight='700')]
    d0, d1 = cx + 215, cx + cw - 20
    dlo, dhi = -4.6, 2.4
    for tick in [-4, -2, 0, 2]:
        xt = xmap(tick, dlo, dhi, d0, d1)
        s += [line(xt, 580, xt, 732, RED if tick == 0 else GRID, 2 if tick == 0 else 1, opacity=.8),
              text(xt, 754, f'{tick:+.0f}', size=13, fill=RED if tick == 0 else MUTED, anchor='middle', weight='700' if tick == 0 else '400')]
    s += [text(d0 + 10, 565, 'negative favors pose', size=13, fill=PURPLE, weight='700'),
          text((d0 + d1) / 2, 780, 'Incremental P3 guarded MAE − B5 guarded MAE', size=13, fill=MUTED, anchor='middle'),
          forest_row(d0, d1, 630, 0.666, -0.589, 1.856, dlo, dhi, 'CMC→P7', color=PURPLE, value=True),
          forest_row(d0, d1, 695, -1.826, -3.968, 0.272, dlo, dhi, 'P7→CMC', color=PURPLE, value=True),
          text(cx + 16, 832, 'Both scaffold-level pose intervals include zero.', size=14, fill=RED, weight='700'),
          text(cx + 16, 858, 'Transfer survives harder extrapolation; pose-specific gain is less certain.', size=13, fill=INK)]
    return svg_document(width, height, 'C', ''.join(s))


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        'figure4A_fixed_replay_independent.svg': panel_a(),
        'figure4B_randomized_routes_independent.svg': panel_b(),
        'figure4C_scaffold_held_out_independent.svg': panel_c(),
    }
    for name, content in outputs.items():
        path = OUT / name
        path.write_text(content, encoding='utf-8')
        print(path)
