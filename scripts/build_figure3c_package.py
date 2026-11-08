#!/usr/bin/env python3
"""Build Figure 3C learning-efficiency artifacts from checked-in data."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/figures/figure3c_data"
SUMMARY = ROOT / "data/expansion/pptl/historical-vs-ai-progressive-comparison.csv"
PLOT_DIR = ROOT / "docs/supporting-information/latex/plot-data"

ROUTES = ["historical_order", "diversity_first", "uncertainty_diversity", "performance_first", "random"]
LABEL = {"historical_order":"Historical order", "diversity_first":"Diversity-first", "uncertainty_diversity":"Uncertainty + diversity", "performance_first":"Performance-first", "random":"Random routes"}
SHORT = {"historical_order":"Historical", "diversity_first":"Diversity", "uncertainty_diversity":"U + D", "performance_first":"Performance", "random":"Random"}
COLOR = {"historical_order":"#667085", "diversity_first":"#7c5cff", "uncertainty_diversity":"#0f766e", "performance_first":"#d97706", "random":"#98a2b3"}
SCOPES = ["P7", "CMC-Por aryl"]
SCOPE_LABEL = {"P7":"Fe(P7)Cl", "CMC-Por aryl":"Fe(CMC-Por)Cl aryl"}

def read_summary():
    with SUMMARY.open(newline="") as f:
        return list(csv.DictReader(f))

def make_summary(rows):
    grouped = {(r["scope"], r["route"]): r for r in rows}
    output = []
    for scope in SCOPES:
        historical = float(grouped[(scope, "historical_order")]["mean_prefix_mae"])
        for route in ROUTES:
            r = grouped[(scope, route)]
            mean = float(r["mean_prefix_mae"])
            output.append({
                "scope": scope, "scope_label": SCOPE_LABEL[scope], "route": route,
                "route_label": LABEL[route], "mean_prefix_mae": mean,
                "auc_mae": float(r["auc_mae"]), "first_prefix_mae": float(r["first_prefix_mae"]),
                "final_prefix_mae": float(r["final_prefix_mae"]), "best_prefix_mae": float(r["best_prefix_mae"]),
                "n90": None if not r["n90"] else int(r["n90"]), "replicates": int(r["replicates"]),
                "rank_by_mean_prefix_mae": int(r["rank_by_mean_prefix_mae"]),
                "historical_mean_prefix_mae": historical,
                "reduction_vs_historical_percent": (historical - mean) / historical * 100,
                "color": COLOR[route],
            })
    return output

def make_trajectories():
    output = []
    for scope, filename in {"P7":"p7_route_progression.csv", "CMC-Por aryl":"cmcpor_route_progression.csv"}.items():
        with (PLOT_DIR / filename).open(newline="") as f:
            for r in csv.DictReader(f):
                n = int(r["n_labeled"])
                for route in ROUTES[:-1]:
                    output.append({"scope":scope, "scope_label":SCOPE_LABEL[scope], "n_labeled":n, "route":route, "route_label":LABEL[route], "mae":float(r[route]), "q25":None, "q75":None})
                output.append({"scope":scope, "scope_label":SCOPE_LABEL[scope], "n_labeled":n, "route":"random", "route_label":LABEL["random"], "mae":float(r["random_mean"]), "q25":float(r["random_q25"]), "q75":float(r["random_q75"])})
    return output

def write_csv(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def svg_summary(summary):
    W, H, left, top, gap = 1280, 650, 92, 86, 68
    panel_w, plot_h, max_mae, max_red = (W-left-44-gap)/2, 390, 24, 65
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="650" viewBox="0 0 1280 650">', '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#15202b}.axis{font-size:14px;fill:#667085}.title{font-size:21px;font-weight:700}.sub{font-size:16px;fill:#475467}.grid{stroke:#e4e7ec}.axisline{stroke:#667085;stroke-width:1.2}.value{font-size:14px;font-weight:700}</style>', '<rect width="100%" height="100%" fill="white"/>', '<text x="92" y="39" class="title">Figure 3C — Learning efficiency under progressive acquisition</text>', '<text x="92" y="64" class="sub">Lower mean-prefix ee MAE is better; reduction is relative to historical source order.</text>']
    for i, scope in enumerate(SCOPES):
        x0 = left + i*(panel_w+gap); px, py, pw = x0+62, top+28, panel_w-78; base = py+plot_h; bar_h = plot_h-64
        out.append(f'<text x="{x0}" y="{top}" class="title">{SCOPE_LABEL[scope]}</text>')
        out.append(f'<text x="{px}" y="{py+18}" class="sub">Mean-prefix MAE (ee points)</text><line x1="{px}" y1="{py+34}" x2="{px}" y2="{base}" class="axisline"/><line x1="{px}" y1="{base}" x2="{px+pw}" y2="{base}" class="axisline"/>')
        for tick in range(0, 25, 5):
            y = base-34-tick/max_mae*bar_h
            out.append(f'<line x1="{px}" y1="{y:.1f}" x2="{px+pw}" y2="{y:.1f}" class="grid"/><text x="{px-12}" y="{y+5:.1f}" text-anchor="end" class="axis">{tick}</text>')
        rows = [r for r in summary if r["scope"] == scope]; step, bw = pw/len(rows), 42
        for j, r in enumerate(rows):
            cx = px+step*(j+.5); bh = r["mean_prefix_mae"]/max_mae*bar_h; y = base-bh; stroke = "#075e54" if r["route"] == "uncertainty_diversity" else "none"; sw = 3 if stroke != "none" else 0
            out.append(f'<rect x="{cx-bw/2:.1f}" y="{y:.1f}" width="{bw}" height="{bh:.1f}" rx="5" fill="{r["color"]}" stroke="{stroke}" stroke-width="{sw}"/><text x="{cx:.1f}" y="{y-8:.1f}" text-anchor="middle" class="value">{r["mean_prefix_mae"]:.1f}</text><text x="{cx:.1f}" y="{base+24}" text-anchor="middle" class="axis">{SHORT[r["route"]]}</text>')
        ry, rbase, rh = base+72, base+110, 58
        out.append(f'<text x="{px}" y="{ry-18}" class="sub">Reduction vs historical (%)</text><line x1="{px}" y1="{rbase}" x2="{px+pw}" y2="{rbase}" class="axisline"/>')
        for j, r in enumerate(rows):
            cx = px+step*(j+.5); h = r["reduction_vs_historical_percent"]/max_red*rh; y = rbase-h
            out.append(f'<rect x="{cx-bw/2:.1f}" y="{y:.1f}" width="{bw}" height="{abs(h):.1f}" rx="4" fill="{r["color"]}" opacity=".9"/><text x="{cx:.1f}" y="{y-7:.1f}" text-anchor="middle" class="axis">{r["reduction_vs_historical_percent"]:.1f}%</text>')
        ud = next(r for r in rows if r["route"] == "uncertainty_diversity")
        out.append(f'<text x="{x0}" y="{H-42}" class="axis">Uncertainty + diversity: {ud["reduction_vs_historical_percent"]:.1f}% lower mean-prefix MAE</text>')
    out.append('</svg>'); return "\n".join(out)

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Figure 3C — Learning efficiency</title><style>body{margin:0;background:#f8fafc;color:#15202b;font:15px Arial,Helvetica,sans-serif}main{max-width:1380px;margin:0 auto;padding:28px 34px 44px;background:white;min-height:100vh}h1{margin:0 0 8px;font-size:27px}.subtitle{color:#475467;margin-bottom:20px}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0 18px}button{border:1px solid #cbd5e1;background:white;border-radius:6px;padding:7px 10px;cursor:pointer}button.active{background:#0f766e;color:white;border-color:#0f766e}#chart{width:100%;overflow:auto}svg{display:block;min-width:980px;width:100%;height:auto}.note{margin-top:16px;padding:12px 14px;background:#f1f5f9;border-left:4px solid #0f766e;line-height:1.45}table{border-collapse:collapse;margin-top:24px;width:100%;font-size:13px}th,td{padding:7px;border-bottom:1px solid #e5e7eb;text-align:right}th:first-child,td:first-child{text-align:left}</style></head><body><main><h1>Figure 3C — Learning efficiency under progressive acquisition</h1><div class="subtitle">Real retrospective Ridge replay data. Lower mean-prefix ee MAE is better; reductions are relative to historical source order.</div><div class="toolbar"><span>View:</span><button id="summaryBtn" class="active">Summary</button><button id="trajectoryBtn">Prefix trajectories</button><button id="downloadBtn">Download SVG</button></div><div id="chart"></div><div class="note"><strong>Interpretation.</strong> Uncertainty + diversity is the best-ranked route in both domains in this retrospective benchmark. This shows learning efficiency on locked observed records; it is not a prospective claim about experimental selectivity.</div><div id="table"></div><script>
const DATA=__PAYLOAD__, scopes=["P7","CMC-Por aryl"], routeOrder=["historical_order","diversity_first","uncertainty_diversity","performance_first","random"], colors=__COLORS__, short=__SHORT__, scopeLabels=__SCOPE_LABEL__;
function drawSummary(){const W=1280,H=650,left=92,top=86,gap=68,panelW=(W-left-44-gap)/2,plotH=390,maxMae=24,maxRed=65;let s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 650"><style>text{font-family:Arial,Helvetica,sans-serif;fill:#15202b}.axis{font-size:14px;fill:#667085}.title{font-size:21px;font-weight:700}.sub{font-size:16px;fill:#475467}.grid{stroke:#e4e7ec}.axisline{stroke:#667085;stroke-width:1.2}.value{font-size:14px;font-weight:700}</style><rect width="100%" height="100%" fill="white"/><text x="92" y="39" class="title">Figure 3C — Learning efficiency under progressive acquisition</text><text x="92" y="64" class="sub">Lower mean-prefix ee MAE is better; reduction is relative to historical source order.</text>';scopes.forEach((scope,i)=>{const x0=left+i*(panelW+gap),px=x0+62,py=top+28,pw=panelW-78,base=py+plotH,barH=plotH-64;s+=`<text x="${x0}" y="${top}" class="title">${scopeLabels[scope]}</text><text x="${px}" y="${py+18}" class="sub">Mean-prefix MAE (ee points)</text><line x1="${px}" y1="${py+34}" x2="${px}" y2="${base}" class="axisline"/><line x1="${px}" y1="${base}" x2="${px+pw}" y2="${base}" class="axisline"/>`;for(let t=0;t<=20;t+=5){const y=base-34-t/maxMae*barH;s+=`<line x1="${px}" y1="${y}" x2="${px+pw}" y2="${y}" class="grid"/><text x="${px-12}" y="${y+5}" text-anchor="end" class="axis">${t}</text>`}const rows=DATA.summary.filter(d=>d.scope===scope),step=pw/rows.length,bw=42;rows.forEach((d,j)=>{const cx=px+step*(j+.5),bh=d.mean_prefix_mae/maxMae*barH,y=base-bh,stroke=d.route==="uncertainty_diversity"?"#075e54":"none";s+=`<rect x="${cx-bw/2}" y="${y}" width="${bw}" height="${bh}" rx="5" fill="${d.color}" stroke="${stroke}" stroke-width="${stroke==="none"?0:3}"/><text x="${cx}" y="${y-8}" text-anchor="middle" class="value">${d.mean_prefix_mae.toFixed(1)}</text><text x="${cx}" y="${base+24}" text-anchor="middle" class="axis">${short[d.route]}</text>`});const ry=base+72,rbase=base+110,rh=58;s+=`<text x="${px}" y="${ry-18}" class="sub">Reduction vs historical (%)</text><line x1="${px}" y1="${rbase}" x2="${px+pw}" y2="${rbase}" class="axisline"/>`;rows.forEach((d,j)=>{const cx=px+step*(j+.5),h=d.reduction_vs_historical_percent/maxRed*rh,y=rbase-h;s+=`<rect x="${cx-bw/2}" y="${y}" width="${bw}" height="${Math.abs(h)}" rx="4" fill="${d.color}" opacity=".9"/><text x="${cx}" y="${y-7}" text-anchor="middle" class="axis">${d.reduction_vs_historical_percent.toFixed(1)}%</text>`});const ud=rows.find(d=>d.route==="uncertainty_diversity");s+=`<text x="${x0}" y="${H-42}" class="axis">Uncertainty + diversity: ${ud.reduction_vs_historical_percent.toFixed(1)}% lower mean-prefix MAE</text>`});s+="</svg>";document.getElementById("chart").innerHTML=s;renderTable()}
function drawTrajectories(){const W=1280,H=650,left=88,top=72,gap=70,panelW=(W-left-40-gap)/2,plotH=470,maxY=45;let s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 650"><style>text{font-family:Arial,Helvetica,sans-serif;fill:#15202b}.axis{font-size:14px;fill:#667085}.title{font-size:21px;font-weight:700}.grid{stroke:#e4e7ec}.axisline{stroke:#667085;stroke-width:1.2}</style><rect width="100%" height="100%" fill="white"/><text x="88" y="34" class="title">Figure 3C — Prefix learning trajectories</text>';scopes.forEach((scope,i)=>{const x0=left+i*(panelW+gap),px=x0+48,py=top+24,pw=panelW-62,base=py+plotH;s+=`<text x="${x0}" y="${top}" class="title">${scopeLabels[scope]}</text><line x1="${px}" y1="${py}" x2="${px}" y2="${base}" class="axisline"/><line x1="${px}" y1="${base}" x2="${px+pw}" y2="${base}" class="axisline"/>`;for(let t=0;t<=40;t+=10){const y=base-t/maxY*plotH;s+=`<line x1="${px}" y1="${y}" x2="${px+pw}" y2="${y}" class="grid"/><text x="${px-10}" y="${y+5}" text-anchor="end" class="axis">${t}</text>`}const rows=DATA.trajectories.filter(d=>d.scope===scope),maxN=Math.max(...rows.map(d=>d.n_labeled));routeOrder.forEach(route=>{const rr=rows.filter(d=>d.route===route);let path="";rr.forEach((d,j)=>{const x=px+(d.n_labeled-2)/(maxN-2)*pw,y=base-d.mae/maxY*plotH;path+=(j?" L ":"M ")+x+" "+y});s+=`<path d="${path}" fill="none" stroke="${colors[route]}" stroke-width="${route==="uncertainty_diversity"?3:2}" opacity="${route==="random"?.55:1}"/>`});s+=`<text x="${px+pw/2}" y="${base+42}" text-anchor="middle" class="axis">Number of labelled substrates</text>`});s+="</svg>";document.getElementById("chart").innerHTML=s;document.getElementById("table").innerHTML=""}
function renderTable(){let h="<table><thead><tr><th>Domain</th><th>Route</th><th>Mean-prefix MAE</th><th>Reduction vs historical</th><th>AUC diagnostic</th><th>Rank</th></tr></thead><tbody>";DATA.summary.forEach(d=>h+=`<tr><td>${d.scope_label}</td><td>${d.route_label}</td><td>${d.mean_prefix_mae.toFixed(3)}</td><td>${d.reduction_vs_historical_percent.toFixed(1)}%</td><td>${d.auc_mae.toFixed(3)}</td><td>${d.rank_by_mean_prefix_mae}/5</td></tr>`);document.getElementById("table").innerHTML=h+"</tbody></table>"}
function downloadSvg(){const svg=document.querySelector("#chart svg");if(!svg)return;const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([svg.outerHTML],{type:"image/svg+xml"}));a.download="figure3c_learning_efficiency.svg";a.click()}
summaryBtn.onclick=()=>{summaryBtn.classList.add("active");trajectoryBtn.classList.remove("active");drawSummary()};trajectoryBtn.onclick=()=>{trajectoryBtn.classList.add("active");summaryBtn.classList.remove("active");drawTrajectories()};downloadBtn.onclick=downloadSvg;drawSummary();</script></main></body></html>'''

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary, trajectories = make_summary(read_summary()), make_trajectories()
    write_csv(OUT / "figure3c_summary.csv", summary)
    write_csv(OUT / "figure3c_prefix_trajectories.csv", trajectories)
    (OUT / "figure3c_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT / "figure3c.svg").write_text(svg_summary(summary))
    html = HTML.replace("__PAYLOAD__", json.dumps({"summary":summary, "trajectories":trajectories}, separators=(",", ":")))
    html = html.replace("__COLORS__", json.dumps(COLOR)).replace("__SHORT__", json.dumps(SHORT)).replace("__SCOPE_LABEL__", json.dumps(SCOPE_LABEL))
    (OUT / "figure3c_learning_efficiency.html").write_text(html)
    manifest = {"figure":"3C", "title":"Learning efficiency under progressive acquisition", "model":"Ridge", "target":"ee_percent", "summary_metric":"mean_prefix_mae", "source_files":["data/expansion/pptl/historical-vs-ai-progressive-comparison.csv", "docs/supporting-information/latex/plot-data/p7_route_progression.csv", "docs/supporting-information/latex/plot-data/cmcpor_route_progression.csv"], "interpretation":"Retrospective learning-efficiency benchmark on locked observed records; not a prospective experimental outcome.", "artifacts":["figure3c.svg", "figure3c_learning_efficiency.html", "figure3c_summary.csv", "figure3c_prefix_trajectories.csv"]}
    (OUT / "figure3c_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote Figure 3C package to {OUT}")

if __name__ == "__main__":
    main()
