import os,sys,csv,statistics,json
from pathlib import Path
from collections import defaultdict
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
P=Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R/'revision/reviewer1_comment1'))
import initial_pair_replay as rr
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

def read(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
for domain in ['p7','cmcpor']:
 out=P/'results'/domain;old=R/'revision/reviewer1_comment1/results/common_test'/domain
 table,active=rr.load(domain);X=table.matrix(rr.FEATURE);idmap={x:i for i,x in enumerate(table.ids)};y=np.array([rr.sp.outcome_value(r.record,'isolated_yield_percent') if rr.sp.outcome_value(r.record,'isolated_yield_percent') is not None else np.nan for r in table.rows]); splits={int(r['split_id']):r for r in read(old/'outer_splits.csv')}
 events=read(out/'yield_selections.csv');pred=read(out/'yield_predictions.csv');scores=read(out/'yield_selected_scores.csv');past=read(old/'selection_events.csv');pr=defaultdict(list)
 for r in pred:
  assert abs(abs(float(r['observed'])-float(r['predicted']))-float(r['abs_error']))<1e-9
  pr[(int(r['split_id']),int(r['pair_id']),r['route'],int(r['replicate']),int(r['budget']))].append(r)
 pastseq=defaultdict(list)
 for r in past:pastseq[(int(r['split_id']),int(r['pair_id']),r['route'],int(r['random_continuation']))].append((int(r['step']),r['substrate_id']))
 overlap={n:[] for n in [6,10,15,20]};refits=0
 for e in events:
  s,j,route,rep=int(e['split_id']),int(e['pair_id']),e['route'],int(e['replicate']);seq=e['selected_ids'].split('|');assert len(seq)==len(set(seq))==20;test=splits[s]['held_out_ids'].split('|');assert not set(seq)&set(test) and set(seq)<=set(splits[s]['candidate_ids'].split('|'))
  oldseq=[x for _,x in sorted(pastseq[s,j,route,rep])]
  assert seq[:2]==oldseq[:2]
  if route in ['historical_order','random']:assert seq==oldseq[:20]
  if route=='uncertainty_diversity':
   for n in overlap:overlap[n].append(len(set(seq[2:n])&set(oldseq[2:n])))
  if s<=2:
   for n in [2,6,10,15,20]:
    t=[idmap[z] for z in seq[:n]];p=pr[s,j,route,rep,n];i=[idmap[z['substrate_id']] for z in p];model=make_pipeline(StandardScaler(),Ridge(alpha=10.,solver='lsqr'));model.fit(X[t],y[t]);values=np.clip(model.predict(X[i]),0,100)
    assert np.max(np.abs(values-np.array([float(z['predicted']) for z in p])))<1e-8;refits+=len(p)
 for row in scores:
  assert abs(float(row['total'])-(.4*float(row['diversity'])+.4*float(row['uncertainty'])+.2*float(row['coverage'])))<1e-10
 summary=read(out/'split_mae.csv');groups=defaultdict(list)
 for r in pred:groups[(int(r['split_id']),r['route'],int(r['budget']))].append(float(r['abs_error']))
 for r in summary:
  if r['endpoint']=='yield':
   a=[statistics.mean(groups[int(r['split_id']),r['route'],n]) for n in [2,6,10,15,20]];assert abs(float(r['mean_mae'])-statistics.mean(a))<1e-9
 diagnosis={'domain':domain,'sequence_overlap_ee_vs_yield':{str(n):{'mean_common_after_initial_pair':statistics.mean(v),'available_new_slots':n-2} for n,v in overlap.items()},'n_prediction_rows_checked':len(pred),'n_trajectories_checked':len(events),'independent_ridge_predictions_refit':refits,'score_rows_checked':len(scores),'locked_cmc_audit_excluded':True,'qualification':'Endpoint trajectories were selected with different labels but evaluated on the same splits and start pairs. Post hoc set overlap is not evidence of causality.'}
 (out/'diagnostics_and_validation.json').write_text(json.dumps(diagnosis,indent=2)+'\n');print(json.dumps(diagnosis,indent=2))
