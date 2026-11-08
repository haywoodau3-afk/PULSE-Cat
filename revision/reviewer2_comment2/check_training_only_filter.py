import os,sys,csv,json
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R));import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from scripts import stage2_full_scope_benchmark as s
rows,names=s.build_feature_rows(P.parent/'reviewer2_comment1/results/p7_source_corrected_copy.jsonl','structure_pose',R/'data/jacs_2025/stage2/features/pose-summary.jsonl',P/'results/corrected_p7_pose_interaction.jsonl','ee');X=np.array([[r['features'].get(n,0.) for n in names] for r in rows]);y=np.array([r['target_value'] for r in rows]);idx={r['substrate_id']:i for i,r in enumerate(rows)};prior=list(csv.DictReader(open(P/'results/corrected_pose_elasticnet_predictions.csv')));splits={mode:{s['split_id']:s for s in (smod(rows))} for mode,smod in [('target',s.build_splits),('family',s.build_family_splits)]};errs=[]
for r in prior:
 split=splits[r['mode']][r['split_id']];train=split['train_indices'];mask=X[train].std(axis=0)>0;z=json.loads(r['selected_params']);model=make_pipeline(StandardScaler(),ElasticNet(alpha=z['alpha'],l1_ratio=z['l1_ratio'],max_iter=20000,random_state=0));model.fit(X[train][:,mask],y[train]);pred=float(model.predict(X[[idx[r['substrate_id']]]][:,mask])[0]);errs.append(abs(pred-float(r['prediction'])))
out={'n_heldout_predictions':len(errs),'maximum_absolute_difference':max(errs),'scope':'For selected Elastic Net models, refitting with training-only nonconstant features and the same chosen hyperparameters; does not reselect hyperparameters or check other estimators.'};(P/'results/train_only_filter_check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
