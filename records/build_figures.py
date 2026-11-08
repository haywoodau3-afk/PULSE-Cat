from pathlib import Path
import json,csv
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;F=P/'figures';F.mkdir(exist_ok=True)
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(n):return ImageFont.truetype(FONT,n)
# Representation plot: matched Elastic Net comparisons with reported conditional intervals.
W,H=1800,1040; im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
d.text((130,55),'Fe(P7)Cl Elastic Net held-out predictions',font=font(46),fill='#14212b')
d.text((130,115),'Corrected pose features; 38 substrates',font=font(28),fill='#3d4c57')
left,right,top,bottom=180,1680,220,850; ymax=20
for y in range(0,21,5):
 yy=bottom-(y/ymax)*(bottom-top);d.line((left,yy,right,yy),fill='#d9e0e4',width=2);d.text((125,yy-16),str(y),font=font(22),fill='#3d4c57')
d.text((36,480),'MAE (ee points)',font=font(25),fill='#26343d')
colors=['#8c9baa','#187b78']; names=['Structure only','Structure + pose']
for i,(mode,title) in enumerate([('target_holdout','Target held out'),('family_holdout','Family held out')]):
 j=json.load(open(P/'full_scope'/f'{mode}_ee_comparison.json'));x=next(z for z in j['model_comparisons'] if z['model_name']=='elastic_net');cx=550+i*760
 for k,(field,lofield,hifield) in enumerate([('structure_only_mae','structure_only_mae_ci95_low','structure_only_mae_ci95_high'),('structure_pose_mae','structure_pose_mae_ci95_low','structure_pose_mae_ci95_high')]):
  val=x[field];lo=x[lofield];hi=x[hifield];x0=cx+(k-.5)*180;barw=140;y0=bottom-(val/ymax)*(bottom-top)
  d.rectangle((x0-barw/2,y0,x0+barw/2,bottom),fill=colors[k]);ylo=bottom-(lo/ymax)*(bottom-top);yhi=bottom-(hi/ymax)*(bottom-top)
  d.line((x0,yhi,x0,ylo),fill='#25343d',width=4);d.line((x0-18,yhi,x0+18,yhi),fill='#25343d',width=4);d.line((x0-18,ylo,x0+18,ylo),fill='#25343d',width=4)
  d.text((x0-36,y0-38),f'{val:.2f}',font=font(23),fill='#14212b')
 d.text((cx-130,885),title,font=font(29),fill='#14212b')
for k,name in enumerate(names):
 x=600+k*470;d.rectangle((x,970,x+30,1000),fill=colors[k]);d.text((x+45,968),name,font=font(23),fill='#26343d')
im.save(F/'figure3_corrected_representation.png',dpi=(300,300))
# Acquisition plot, corrected common-test means across 20 overlapping splits.
W,H=2200,1130; im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
d.text((100,45),'Corrected common-test acquisition baselines',font=font(46),fill='#14212b')
d.text((100,110),'Mean ee MAE across 20 overlapping retrospective splits',font=font(27),fill='#3d4c57')
methods=['historical_order','uncertainty_diversity','random','qbc','expected_improvement','thompson'];labels=['Source\norder','Uncertainty–\ndiversity','Random','Query by\ncommittee','Expected\nimprovement','Thompson']
for panel,domain,title in [(0,'p7','Fe(P7)Cl'),(1,'cmcpor','Fe(CMC-Por)Cl aryl cohort')]:
 left=130+panel*1050;right=left+930;top=235;bottom=820; ymax=22
 for y in range(0,23,5):
  yy=bottom-y/ymax*(bottom-top);d.line((left,yy,right,yy),fill='#d9e0e4',width=2)
  if panel==0:d.text((80,yy-14),str(y),font=font(21),fill='#3d4c57')
 rows=list(csv.DictReader(open(P.parent/'reviewer2_comment2'/'results'/'corrected_baselines'/domain/'summary.csv'))); lookup={r['route']:float(r['mean_mae']) for r in rows};vals=[lookup[m] for m in methods]
 pts=[]
 for k,val in enumerate(vals):
  x=left+55+k*160;y=bottom-val/ymax*(bottom-top);pts.append((x,y))
  col='#b0473c' if k==1 else '#237a78';d.ellipse((x-12,y-12,x+12,y+12),fill=col,outline='white',width=2);d.text((x-38,y-47),f'{val:.2f}',font=font(22),fill='#14212b')
 d.line(pts,fill='#82969f',width=4)
 d.text((left+270,180),title,font=font(30),fill='#14212b')
 for k,label in enumerate(labels):
  x=left+55+k*160;d.multiline_text((x-47,845),label,font=font(19),fill='#26343d',align='center',spacing=2)
d.text((100,1065),'Lower is better. Each panel compares methods on common test records; split sets overlap.',font=font(22),fill='#3d4c57')
im.save(F/'figure6_corrected_acquisition.png',dpi=(300,300))
