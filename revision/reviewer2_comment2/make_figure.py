import os,sys,json,math,shutil,hashlib
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT));from scripts import stage2_pose_interaction as si
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from rdkit import Chem
from rdkit.Chem import Draw,AllChem
from rdkit.Chem.Draw import rdMolDraw2D
M=json.load(open(P/'results/example_audit.json'))['examples']; corrected=json.load(open(P/'results/corrected_example_details.json')); OUT=P/'results';OUT.mkdir(exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def F(n,b=False):return ImageFont.truetype(bold if b else font,n)
def title(draw,x,y,s,n=36,b=False,fill='#17202a'):draw.text((x,y),s,font=F(n,b),fill=fill)
def chem(sid):
 r=M[sid];m=Chem.MolFromSmiles(r['substrate_smiles']);assert m;AllChem.Compute2DCoords(m);Chem.MolToMolFile(m,str(OUT/f'{sid}_substrate.mol'));drawing=rdMolDraw2D.MolDraw2DSVG(850,440);drawing.drawOptions().bondLineWidth=2;drawing.DrawMolecule(m);drawing.FinishDrawing();(OUT/f'{sid}_substrate.svg').write_text(drawing.GetDrawingText());return Draw.MolToImage(m,size=(850,440))
# Orthographic view in the shared frozen-core coordinates; only catalyst heavy atoms within 6.5 A of Fe shown.
ax=math.radians(63);az=math.radians(21);Rx=np.array([[1,0,0],[0,math.cos(ax),-math.sin(ax)],[0,math.sin(ax),math.cos(ax)]]);Rz=np.array([[math.cos(az),-math.sin(az),0],[math.sin(az),math.cos(az),0],[0,0,1]]);rot=Rx@Rz
colors={'C':(89,100,112),'N':(46,95,174),'O':(207,74,67),'S':(230,177,40),'Cl':(83,161,79),'Fe':(186,101,30)}
radii={'C':.76,'N':.71,'O':.66,'S':1.05,'Cl':1.02,'Fe':1.24,'F':.57,'P':1.07}
def pose(sid,accent):
 info=M[sid];atoms=si.parse_xyz(ROOT/info['assembly_xyz']);core=info['frozen_core_atom_count'];assert core==214
 xyz=np.array([a['xyz'] for a in atoms]);symbols=[a['element'] if 'element' in a else a.get('symbol') for a in atoms]
 # The parser uses element; check data explicitly.
 if any(x is None for x in symbols):raise ValueError(atoms[0])
 fe=46;assert symbols[fe]=='Fe';nit=si.stage1_pose_molecule(info['nitrene_smiles']);mapping=si.stage1_index_to_assembly_index(nit,core);sub=[mapping[a.GetIdx()] for a in nit.GetAtoms() if a.GetAtomicNum()>1];coreids=[i for i in range(core) if symbols[i]!='H' and np.linalg.norm(xyz[i]-xyz[fe])<=6.5];assert fe in coreids
 coreb=[]
 for ai,i in enumerate(coreids):
  for j in coreids[ai+1:]:
   if 'Fe' in (symbols[i],symbols[j]):continue
   dist=np.linalg.norm(xyz[i]-xyz[j]);th=1.20*(radii.get(symbols[i],.76)+radii.get(symbols[j],.76))
   if .65<dist<th:coreb.append((i,j))
 bonds=[(mapping[b.GetBeginAtomIdx()],mapping[b.GetEndAtomIdx()]) for b in nit.GetBonds() if b.GetBeginAtom().GetAtomicNum()>1 and b.GetEndAtom().GetAtomicNum()>1]
 nidx=mapping[info['pose_nitrene_index_zero_based']];rc=mapping[info['pose_reactive_c_index_zero_based']];assert symbols[nidx]=='N' and symbols[rc]=='C'
 # Snapshot includes only Fe-neighbour catalyst context and all substrate heavy atoms, with fixed camera and scale.
 points=(xyz-xyz[fe])@rot.T;w,h=850,600;scale=50;cx,cy=w/2,h/2+10
 def proj(i):return (float(cx+scale*points[i,0]),float(cy-scale*points[i,1]))
 im=Image.new('RGB',(w,h),'white');dr=ImageDraw.Draw(im)
 for i,j in sorted(coreb,key=lambda v:(points[v[0],2]+points[v[1],2])/2):dr.line([proj(i),proj(j)],fill='#d1d7db',width=5)
 for i in sorted(coreids,key=lambda v:points[v,2]):
  if i==fe:continue
  x,y=proj(i);rad=5;dr.ellipse((x-rad,y-rad,x+rad,y+rad),fill='#c4ccd0')
 # Explicit Fe–N bond is geometric association, not a generated transition state.
 dr.line([proj(fe),proj(nidx)],fill='#8b7056',width=5)
 for i,j in sorted(bonds,key=lambda v:(points[v[0],2]+points[v[1],2])/2):
  dr.line([proj(i),proj(j)],fill=accent,width=12)
 for i in sorted(sub+[fe],key=lambda v:points[v,2]):
  x,y=proj(i);sym=symbols[i];rad=17 if i==fe else 12 if sym=='N' else 10;col=colors['Fe'] if i==fe else colors.get(sym,(62,107,150)) if sym!='C' else accent
  dr.ellipse((x-rad,y-rad,x+rad,y+rad),fill=col,outline='#29343b',width=2)
 # Ring identifies the reported reactive C, not a transition state.
 x,y=proj(rc);dr.ellipse((x-17,y-17,x+17,y+17),outline='#1c9a58',width=4)
 return im
fig=Image.new('RGB',(1860,1590),'white');d=ImageDraw.Draw(fig)
title(d,60,32,'Illustrative matched substrate examples',44,True)
title(d,60,94,'Fe(P7)Cl, 60 °C; source-reported ee and target-held-out Elastic Net predictions',27)
for col,sid,accent in [(0,'1a',(29,130,125)),(1,'1ah',(143,80,155))]:
 x=55+col*930;info=M[sid];title(d,x,154,f'{sid} → {info["product_id"]}',36,True)
 title(d,x,202,'Starting aryl azide (2D)',25,True);fig.paste(chem(sid),(x,235))
 title(d,x,662,'Sampled Fe-bound nitrene assembly (3D)',25,True);fig.paste(pose(sid,accent),(x,700))
 # measured 2a/2ah and prediction result. 
 title(d,x,1320,f'Observed |ee|: {info["ee_percent"]}%',30,True)
 v=info['prediction'];title(d,x,1362,'Held-out prediction: structure  '+f'{v["target_structure"]["prediction"]:.1f}%'+'   |   + pose  '+f'{corrected[sid]["models"]["target"]["prediction"]:.1f}%',24)
 if col==0: d.line([(920,155),(920,1410)],fill='#dde2e5',width=2)
title(d,60,1453,'Green ring: reported reactive carbon   •   orange: Fe   •   blue: nitrene N',25)
title(d,60,1492,'Gray: proximal frozen catalyst heavy atoms; H and distal catalyst atoms omitted.',25)
title(d,60,1528,'Rank-1 UFF sampled assemblies; illustrations are not transition states or populations.',25)
fig.save(OUT/'substrate_examples.png',dpi=(300,300))
for sid in M:
 info=M[sid];shutil.copy2(ROOT/info['assembly_xyz'],OUT/f'{sid}_selected_assembly.xyz');shutil.copy2(ROOT/info['substrate_sdf'],OUT/f'{sid}_selected_nitrene.sdf')
print('wrote',OUT/'substrate_examples.png')
