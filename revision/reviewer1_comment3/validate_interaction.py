import sys,csv,json,statistics
from pathlib import Path
from collections import defaultdict
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'reviewer1_comment2'))
import weight_sensitivity as ws
rr=ws.rr;sp=ws.sp
for domain in ('p7','cmcpor'):
 out=HERE/'results'/domain;table,active=rr.load(domain);design=ws.load_design(domain,table,active)
 def read(p):
  with p.open(newline='') as f:return list(csv.DictReader(f))
 preds=read(out/'predictions.csv');seqs=read(out/'structure_sequences.csv'); splits=read(out/'split_results.csv');old=read(HERE.parent/'reviewer1_comment1'/'results'/'common_test'/domain/'split_results.csv')
 designmap={s:(set(table.ids[i] for i in test),set(table.ids[i] for i in pool)) for s,test,pool,pairs in design}
 groups=defaultdict(list)
 for r in preds:
  test,pool=designmap[int(r['split_id'])];assert r['substrate_id'] in test
  err=abs(float(r['observed'])-float(r['predicted']));assert abs(err-float(r['absolute_error']))<1e-9
  groups[(int(r['split_id']),r['representation'],r['route'])].append(err)
 for r in splits:
  s=int(r['split_id'])
  for f in ('structure','pose'):
   for route in ('historical_order','uncertainty_diversity','random'):
    assert abs(statistics.mean(groups[(s,f,route)])-float(r[f+'_'+route]))<1e-9
  x=old[s-1]
  for route,k in [('historical_order','source_mae'),('uncertainty_diversity','ud_mae'),('random','random_mae')]:assert abs(float(r['pose_'+route])-float(x[k]))<1e-9
 ids={v:i for i,v in enumerate(table.ids)}; X=table.matrix('rdkit_morgan'); y=np.array([sp.outcome_value(r.record,'ee_percent') if sp.outcome_value(r.record,'ee_percent') is not None else np.nan for r in table.rows]); checks=0
 for row in seqs:
  if int(row['split_id']) not in (1,10,20) or int(row['pair_id'])!=1 or int(row['replicate'])!=0:continue
  s=int(row['split_id']);test,pool=designmap[s]; sequence=row['ids'].split('|');assert set(sequence)<=pool and len(set(sequence))==20
  for n in (2,10,20):
   train=[ids[x] for x in sequence[:n]]; subset=[r for r in preds if int(r['split_id'])==s and int(r['pair_id'])==1 and r['representation']=='structure' and r['route']==row['route'] and int(r['replicate'])==0 and int(r['budget'])==n]
   m=make_pipeline(StandardScaler(),Ridge(alpha=10.0,solver='lsqr'));m.fit(X[train],y[train]);expected=np.clip(m.predict(X[[ids[r['substrate_id']] for r in subset]]),0,100)
   assert np.allclose(expected,[float(r['predicted']) for r in subset],atol=1e-9);checks+=len(subset)
 print(domain,'prediction rows',len(preds),'all aggregate metrics and heldout membership passed, original pose metrics matched, independent structure predictions checked',checks)
