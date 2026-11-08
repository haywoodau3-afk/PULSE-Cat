#!/usr/bin/env python3
import os,sys,csv,json,random,statistics,hashlib,time
from pathlib import Path
from collections import defaultdict
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'))
import initial_pair_replay as rr
import numpy as np
from scipy.stats import spearmanr
sp=rr.sp;B=(2,6,10,15,20);SEEDS={'p7':20261108,'cmcpor':20261109}
def read(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 assert rows
 with open(p,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
def main(domain):
 start=time.time();old=ROOT/'revision/reviewer1_comment1/results/common_test'/domain;out=P/'results'/domain;out.mkdir(parents=True,exist_ok=True)
 table,active=rr.load(domain); X=table.matrix(rr.FEATURE);ids=table.ids; idx={v:i for i,v in enumerate(ids)}
 y=np.array([sp.outcome_value(r.record,'isolated_yield_percent') if sp.outcome_value(r.record,'isolated_yield_percent') is not None else np.nan for r in table.rows]);ee=np.array([sp.outcome_value(r.record,'ee_percent') if sp.outcome_value(r.record,'ee_percent') is not None else np.nan for r in table.rows]);assert all(np.isfinite(y[i]) and np.isfinite(ee[i]) for i in active)
 splits=read(old/'outer_splits.csv'); pairs=read(old/'initial_pairs.csv'); assert len(splits)==20 and len(pairs)==60
 pred=[];events=[];scores=[]
 for row in splits:
  s=int(row['split_id']);test=[idx[x] for x in row['held_out_ids'].split('|')];pool=[idx[x] for x in row['candidate_ids'].split('|')];assert set(test).isdisjoint(pool) and set(test+pool)==set(active)
  for pr in [p for p in pairs if int(p['split_id'])==s]:
   j=int(pr['pair_id']);pair=[idx[pr['substrate_1']],idx[pr['substrate_2']]];assert set(pair)<=set(pool)
   for route,rep in [('historical_order',0),('uncertainty_diversity',0),('random',0),('random',1),('random',2)]:
    seed=SEEDS[domain]*10000+s*100+j*10+rep; rng=random.Random(seed);sel=list(pair)
    for n in range(2,21):
     if n in B:
      ps=sp.audit_prediction_rows(table,X,y,sel,test,route,rep,'isolated_yield_percent',n);ps=[x for x in ps if x['model']=='ridge'];assert len(ps)==len(test)
      for z in ps:pred.append({'domain':domain,'split_id':s,'pair_id':j,'route':route,'replicate':rep,'budget':n,'substrate_id':z['substrate_id'],'observed':z['observed_value'],'predicted':z['predicted_value'],'abs_error':abs(z['observed_value']-z['predicted_value'])})
     if n==20:break
     candidates=[i for i in pool if i not in sel]
     if route=='historical_order':chosen=min(candidates,key=lambda i:table.rows[i].source_order)
     elif route=='random':chosen=candidates[rng.randrange(len(candidates))]
     else:
      score,components=sp.selection_components(table,X,y,sel,candidates,route);k=max(range(len(candidates)),key=lambda k:(score[k],-table.rows[candidates[k]].source_order));chosen=candidates[k]
      scores.append({'split_id':s,'pair_id':j,'budget':n,'selected_id':ids[chosen],'diversity':float(components['diversity_score'][k]),'uncertainty':float(components['uncertainty_score'][k]),'coverage':float(components['family_coverage_score'][k]),'total':float(score[k])})
     sel.append(chosen)
    events.append({'domain':domain,'split_id':s,'pair_id':j,'route':route,'replicate':rep,'seed':seed,'selected_ids':'|'.join(ids[i] for i in sel),'mean_selected_yield_at_20':float(np.mean(y[sel]))})
  print(domain,'split',s,'elapsed',round(time.time()-start,1),flush=True)
 write(out/'yield_predictions.csv',pred);write(out/'yield_selections.csv',events);write(out/'yield_selected_scores.csv',scores)
 ep=read(old/'predictions.csv'); grouped=defaultdict(list)
 for r in pred:grouped[('yield',r['split_id'],r['route'],r['budget'])].append(float(r['abs_error']))
 for r in ep:grouped[('ee',int(r['split_id']),r['route'],int(r['n_labeled']))].append(float(r['absolute_error']))
 summary=[]
 for endpoint in ('yield','ee'):
  for s in range(1,21):
   for route in ('historical_order','uncertainty_diversity','random'):
    ms=[statistics.mean(grouped[(endpoint,s,route,n)]) for n in B];summary.append({'domain':domain,'endpoint':endpoint,'split_id':s,'route':route,'mean_mae':statistics.mean(ms),**{f'mae_{n}':v for n,v in zip(B,ms)}})
 write(out/'split_mae.csv',summary)
 lookup={(r['endpoint'],r['split_id'],r['route']):r['mean_mae'] for r in summary};contrasts=[]
 for endpoint in ('yield','ee'):
  for route in ('historical_order','random'):
   ds=[lookup[endpoint,s,route]-lookup[endpoint,s,'uncertainty_diversity'] for s in range(1,21)]
   contrasts.append({'domain':domain,'endpoint':endpoint,'comparator':route,'mean_comparator_mae':statistics.mean(lookup[endpoint,s,route] for s in range(1,21)),'mean_ud_mae':statistics.mean(lookup[endpoint,s,'uncertainty_diversity'] for s in range(1,21)),'mean_difference':statistics.mean(ds),'median_difference':statistics.median(ds),'splits_favour_ud':sum(x>1e-10 for x in ds),'splits_favour_comparator':sum(x< -1e-10 for x in ds),'min_difference':min(ds),'max_difference':max(ds)})
 write(out/'contrasts.csv',contrasts)
 oldev=read(old/'selection_events.csv');es=defaultdict(list)
 for r in oldev:
  if r['route']=='uncertainty_diversity':es[int(r['split_id']),int(r['pair_id'])].append((int(r['step']),r['substrate_id']))
 overlaps=[]
 for r in events:
  if r['route']=='uncertainty_diversity':
   prev=[i for _,i in sorted(es[r['split_id'],r['pair_id']])];current=r['selected_ids'].split('|');assert prev[:2]==current[:2];overlaps.append(len(set(prev[2:20])&set(current[2:20])))
 meta={'domain':domain,'paired_n':len(active),'yield_min_max':[float(np.min(y[active])),float(np.max(y[active]))],'yield_median':float(np.median(y[active])),'yield_iqr':[float(i) for i in np.quantile(y[active],[.25,.75])],'ee_yield_spearman':float(spearmanr(ee[active],y[active]).statistic),'ud_common_selections_after_two_starts_to_budget20_mean':statistics.mean(overlaps),'yield_mean_selected_at_budget20':{route:statistics.mean(r['mean_selected_yield_at_20'] for r in events if r['route']==route) for route in ('historical_order','uncertainty_diversity','random')},'input_hashes':{rr.CONFIG[domain][k]:rr.sha(ROOT/rr.CONFIG[domain][k]) for k in ['records','features']},'prior_splits_hash':rr.sha(old/'outer_splits.csv'),'prior_ee_predictions_hash':rr.sha(old/'predictions.csv'),'code_hash':rr.sha(Path(__file__)),'seed':SEEDS[domain],'budgets':B,'seconds':time.time()-start,'notes':'Common held-out sets; existing ee trajectories reused. Repeated overlapping splits, descriptive only; selected outcomes revealed only after selection.'}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2),flush=True)
if __name__=='__main__':main(sys.argv[1])
