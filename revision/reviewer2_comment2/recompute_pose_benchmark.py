import os,sys,csv,json,time,statistics
from pathlib import Path
from collections import defaultdict
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts import stage2_full_scope_benchmark as s
start=time.time();rows,names=s.build_feature_rows(P.parent/'reviewer2_comment1/results/p7_source_corrected_copy.jsonl','structure_pose',ROOT/'data/jacs_2025/stage2/features/pose-summary.jsonl',P/'results/corrected_p7_pose_interaction.jsonl','ee');assert len(rows)==38
X,y=s.matrix_arrays(rows,names);index={r['substrate_id']:i for i,r in enumerate(rows)};report=ROOT/'data/jacs_2025/stage2/reports';grid=s.model_grid()['elastic_net'];out=[]
for mode in ['target','family']:
 splits=s.build_splits(rows) if mode=='target' else s.build_family_splits(rows)
 prior=json.load(open(report/('full-scope-structure-splits.json' if mode=='target' else 'family-heldout-ee-splits.json')))['splits'];lookup={x['split_id']:x for x in prior};assert len(splits)==len(prior)
 for i,split in enumerate(splits):
  old=lookup[split['split_id']];assert split['train_substrate_ids']==old['train_substrate_ids'] and split['validation_substrate_ids']==old['validation_substrate_ids'];chosen=s.choose_model('elastic_net',grid,split,X,y);tar=split.get('target_indices',[split['target_index']]);pred,_=s.fit_predict(chosen['estimator'],X[split['train_indices']],y[split['train_indices']],X[tar]);
  for j,idx in enumerate(tar):out.append({'mode':mode,'split_id':split['split_id'],'substrate_id':rows[idx]['substrate_id'],'observed_ee':float(y[idx]),'prediction':float(pred[j]),'abs_error':abs(float(pred[j]-y[idx])),'selected_params':chosen['estimator_params']})
  if i%8==0:print(mode,'fold',i+1,'/',len(splits),'time',round(time.time()-start,1),flush=True)
res=P/'results';res.mkdir(exist_ok=True)
with (res/'corrected_pose_elasticnet_predictions.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
summary={}
for mode in ['target','family']:
 q=[r for r in out if r['mode']==mode];assert len(q)==38;mae=statistics.mean(r['abs_error'] for r in q);old=12.612277273402894 if mode=='target' else 10.405627 # structure-only old
 summary[mode]={'n':len(q),'corrected_pose_mae':mae,'structure_only_mae_rounded':12.612 if mode=='target' else 10.406,'note':'same archived train/validation memberships; P7 pose-interaction fields corrected; label-blind global variance filter retained for comparability'}
(res/'corrected_pose_benchmark_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
