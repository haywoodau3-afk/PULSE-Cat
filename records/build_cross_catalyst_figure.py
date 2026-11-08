from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;F=P/'figures';F.mkdir(exist_ok=True);fontp='/System/Library/Fonts/Supplemental/Arial.ttf'
def ft(n):return ImageFont.truetype(fontp,n)
p=np.load(P/'stage2pp_p7/density/1i.npz')['nitrene__all_heavy__all_200'];c=np.load(P/'stage2pp_cmc/density/2r.npz')['nitrene__all_heavy__all_200']
def norm(a):
 a=np.maximum(a,0).astype(float);return a/a.sum()
pn=norm(p);cn=norm(c)
scan=json.loads((P/'corrected_project'/'cross_catalyst_occupancy_scan.json').read_text())
pair=scan['previously_illustrated_pair']
bc=float(pair['bhattacharyya_coefficient']);tv=float(pair['total_variation_distance']);js=float(pair['jensen_shannon_divergence_bits']);rank=int(pair['corrected_js_rank'])
report={'pair':['1i','2r'],'feature':'Stage 2pp nitrene-centered all-heavy-atom occupancy, all 200 poses','normalization':'Each non-negative occupancy grid normalized to unit sum before overlap','bhattacharyya_coefficient':bc,'total_variation_distance':tv,'jensen_shannon_divergence_bits':js,'corrected_rank_among_13':rank,'corrected_scan':str((P/'corrected_project'/'cross_catalyst_occupancy_scan.json').relative_to(P)),'interpretation_limit':scan['interpretation_limit']}
(P/'corrected_project'/'cross_catalyst_occupancy.json').write_text(json.dumps(report,indent=2)+'\n')
W,H=1700,850;im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im);d.text((100,45),'Corrected sampled occupancy for a shared substrate identity',font=ft(42),fill='#14212b');d.text((100,102),'Nitrene-centered all-heavy-atom occupancy; 200 poses; each grid normalised to unit sum',font=ft(25),fill='#3d4c57')
arr=[pn,cn];titles=['Fe(P7)Cl substrate 1i','Fe(CMC-Por)Cl substrate 2r'];xstarts=[170,900];ytop=240;cell=18
for a,title,x0 in zip(arr,titles,xstarts):
 d.text((x0,170),title,font=ft(28),fill='#14212b');maxv=float(max(pn.max(),cn.max()))
 for iy in range(a.shape[0]):
  for ix in range(a.shape[1]):
   t=float(a[iy,ix]/maxv) if maxv else 0
   # white to teal color ramp
   rgb=(int(248-175*t),int(250-104*t),int(250-94*t))
   x=x0+ix*cell;y=ytop+iy*cell;d.rectangle((x,y,x+cell-1,y+cell-1),fill=rgb)
 d.rectangle((x0,ytop,x0+a.shape[1]*cell,ytop+a.shape[0]*cell),outline='#45545e',width=2)
 d.text((x0,ytop+a.shape[0]*cell+17),'40 axial × 20 radial bins; z −8 to 12 Å; ρ 0 to 10 Å',font=ft(18),fill='#45545e')
d.text((100,785),f'Corrected rank {rank}/13; JS = {js:.4f} bits; TV = {tv:.4f}; Bhattacharyya overlap = {bc:.4f}. Descriptor-field comparison, not a measured conformer population or mechanism.',font=ft(20),fill='#26343d')
im.save(F/'figure5_corrected_cross_catalyst.png',dpi=(300,300))
