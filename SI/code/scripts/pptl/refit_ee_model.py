"""Refit the development ee model after a complete sealed-panel reveal."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.linear_model import Ridge

def fp(s):
 m=Chem.MolFromSmiles(s); return np.asarray(AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=2048),dtype=float)

def main():
 p=argparse.ArgumentParser(); p.add_argument('--records',type=Path,nargs='+',required=True); p.add_argument('--revealed-panel',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); x=[]; y=[]
 for path in a.records:
  for line in path.read_text().splitlines():
   if not line.strip(): continue
   r=json.loads(line); ee=r.get('outcome',{}).get('ee_percent'); s=r.get('structure',{}).get('atom_mapped_substrate_smiles')
   if isinstance(ee,(int,float)) and s: x.append(fp(s)); y.append(float(ee))
 panel=list(csv.DictReader(a.revealed_panel.open(encoding='utf-8')))
 if any(r.get('outcome_revealed')!='true' for r in panel) or any(not r.get('outcome_ee','').strip() for r in panel): raise SystemExit('revealed panel incomplete')
 for r in panel: x.append(fp(r['canonical_smiles'])); y.append(float(r['outcome_ee']))
 model=Ridge(alpha=10).fit(np.asarray(x),np.asarray(y)); pred=model.predict(np.asarray(x)); report={'historical_count':len(y)-len(panel),'revealed_panel_count':len(panel),'refit_count':len(y),'training_mae':float(np.abs(pred-np.asarray(y)).mean()),'status':'refit_complete','note':'training MAE is descriptive; use untouched audit/prospective data for evaluation'}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
