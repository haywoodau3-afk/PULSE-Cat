"""Retrospective sequential ee-acquisition dry run on labelled substrates."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.linear_model import Ridge


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--records", type=Path, nargs="+", required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); rows=[]
    for path in args.records:
        for line in path.read_text().splitlines():
            if not line.strip(): continue
            r=json.loads(line); ee=r.get('outcome',{}).get('ee_percent'); smi=r.get('structure',{}).get('atom_mapped_substrate_smiles')
            if isinstance(ee,(int,float)) and smi:
                m=Chem.MolFromSmiles(smi); rows.append((r.get('substrate_id'),float(ee),np.asarray(AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=2048),dtype=float)))
    random.Random(1101).shuffle(rows); x=np.asarray([r[2] for r in rows]); y=np.asarray([r[1] for r in rows]); selected=list(range(min(4,len(rows)))); remaining=list(range(4,len(rows))); trajectory=[]
    while remaining and len(trajectory)<8:
        model=Ridge(alpha=10).fit(x[selected],y[selected]); preds=model.predict(x[remaining]); errors=np.abs(preds-y[remaining]); trajectory.append({'prefix_size':len(selected),'test_mae':float(errors.mean()),'selected_ids':[rows[i][0] for i in remaining[:4]]})
        take=remaining[:4]; selected.extend(take); remaining=remaining[4:]
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'n_labelled':len(rows),'trajectory':trajectory,'interpretation':'retrospective dry run; labels are historical and no generated-candidate outcomes were used'},indent=2)+'\n'); print(json.dumps({'n_labelled':len(rows),'steps':len(trajectory)},indent=2)); return 0

if __name__ == '__main__': raise SystemExit(main())
