"""Cross-fitted ee acquisition comparison against a random baseline."""
from __future__ import annotations
import argparse,json,random
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

def main():
 p=argparse.ArgumentParser(); p.add_argument('--records',type=Path,nargs='+',required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); rows=[]
 for path in a.records:
  for line in path.read_text().splitlines():
   if not line.strip(): continue
   r=json.loads(line); y=r.get('outcome',{}).get('ee_percent'); s=r.get('structure',{}).get('atom_mapped_substrate_smiles')
   if isinstance(y,(int,float)) and s:
    m=Chem.MolFromSmiles(s); rows.append((r.get('substrate_id'),float(y),np.asarray(AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=2048),dtype=float)))
 x=np.asarray([r[2] for r in rows]); y=np.asarray([r[1] for r in rows]); pred=np.zeros(len(rows)); k=KFold(5,shuffle=True,random_state=1101)
 for tr,te in k.split(x): pred[te]=Ridge(alpha=10).fit(x[tr],y[tr]).predict(x[te])
 order=np.argsort(-pred); random_order=list(range(len(rows))); random.Random(1101).shuffle(random_order); out={}
 for name,idx in [('ee_aware',order),('random',random_order)]:
  curve=[]
  for n in (4,8,16,24,32): curve.append({'n':n,'mae':float(np.abs(pred[idx[:n]]-y[idx[:n]]).mean()),'mean_observed_ee':float(y[idx[:n]].mean())})
  out[name]=curve
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps({'n_labelled':len(rows),'method':'5-fold out-of-fold Ridge predictions','curves':out},indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
