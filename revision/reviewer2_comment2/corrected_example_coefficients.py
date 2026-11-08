import os,sys,csv,json,statistics
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT));import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from scripts import stage2_full_scope_benchmark as s
rows,names=s.build_feature_rows(P.parent/'reviewer2_comment1/results/p7_source_corrected_copy.jsonl','structure_pose',ROOT/'data/jacs_2025/stage2/features/pose-summary.jsonl',P/'results/corrected_p7_pose_interaction.jsonl','ee');raw=np.array([[r['features'].get(n,0.) for n in names] for r in rows]);active=raw.std(axis=0)>0;X=raw[:,active];names=np.array(names)[active];y=np.array([r['target_value'] for r in rows]);index={r['substrate_id']:i for i,r in enumerate(rows)}
def read(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
new=read(P/'results/corrected_pose_elasticnet_predictions.csv');results={}
for sid in ['1a','1ah']:
 rr=next(r for r in rows if r['substrate_id']==sid);k1='pose_interaction.substrate_centroid_to_fe_distance_angstrom.mean';k2='pose_interaction.nitrene_n_to_reported_c_distance_angstrom.mean';results[sid]={'features':{k:rr['features'][k] for k in [k1,k2]},'models':{}}
 for mode in ['target','family']:
  oldfile=ROOT/'data/jacs_2025/stage2/reports'/('full-scope-structure-pose-model-predictions.csv' if mode=='target' else 'family-heldout-structure-pose-ee-model-predictions.csv');prev=next(r for r in read(oldfile) if r['target_substrate_id']==sid and r['model_name']=='elastic_net' and r['target_name']=='ee');updated=next(r for r in new if r['substrate_id']==sid and r['mode']==mode);params=json.loads(updated['selected_params']);train=[index[x] for x in prev['train_substrate_ids'].split('|')];m=make_pipeline(StandardScaler(),ElasticNet(alpha=params['alpha'],l1_ratio=params['l1_ratio'],max_iter=20000,random_state=0));m.fit(X[train],y[train]);assert abs(float(m.predict(X[[index[sid]]])[0])-float(updated['prediction']))<1e-7
  results[sid]['models'][mode]={'prediction':float(updated['prediction']),'coefficients':{k:float(m[-1].coef_[list(names).index(k)]) for k in [k1,k2]}}
(P/'results/corrected_example_details.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
