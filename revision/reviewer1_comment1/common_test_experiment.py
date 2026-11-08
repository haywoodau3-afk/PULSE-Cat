#!/usr/bin/env python3
"""Prespecified repeated common-test-set sensitivity analysis.

Only the revision folder is written. The existing acquisition and prediction
functions are used, while an outer holdout is excluded from the candidate pool.
"""
import argparse,csv,hashlib,itertools,json,random,statistics,sys,time
from collections import defaultdict
from pathlib import Path
import numpy as np
import initial_pair_replay as rr
sp=rr.sp
ROOT=rr.ROOT
OUT=rr.DEST/'common_test'
BUDGETS=(2,6,10,15,20)
SPLITS=20
PAIRS_PER_SPLIT=3
RANDOM_RUNS=3
SEEDS={'p7':20261108,'cmcpor':20261109}
TEST_SIZES={'p7':6,'cmcpor':5}

def split_design(table,active,domain):
 rng=random.Random(SEEDS[domain]); seen=set();out=[]
 while len(out)<SPLITS:
  test=tuple(sorted(rng.sample(active,TEST_SIZES[domain])))
  if test in seen:continue
  seen.add(test);pool=[i for i in active if i not in test]
  pairs=rng.sample(list(itertools.combinations(pool,2)),PAIRS_PER_SPLIT)
  out.append((test,pool,pairs))
 return out

def simulate(table,pool,test,pair,route,seed):
 """Reproduce selection rules through 20 labels and score fixed test records."""
 assert len(set(pair))==2 and set(pair)<=set(pool) and not set(test)&set(pool)
 selected=list(pair);events=list(selected);rng=random.Random(seed)
 X=table.matrix(rr.FEATURE);y=np.asarray([sp.outcome_value(r.record,'ee_percent') if sp.outcome_value(r.record,'ee_percent') is not None else np.nan for r in table.rows],dtype=float)
 predictions=[]
 for n in range(2,max(BUDGETS)+1):
  if n in BUDGETS:
   v=sp.audit_prediction_rows(table,X,y,selected,test,route,0,'ee_percent',n)
   q=[r for r in v if r['model']=='ridge']
   assert len(q)==len(test) and all(r['observed_value'] is not None for r in q)
   predictions.extend(q)
  if n==max(BUDGETS):break
  candidates=[i for i in pool if i not in selected]
  if route=='historical_order':chosen=min(candidates,key=lambda i:table.rows[i].source_order)
  elif route=='random':chosen=candidates[rng.randrange(len(candidates))]
  elif route=='uncertainty_diversity':
   scores,_=sp.selection_components(table,X,y,selected,candidates,route)
   chosen=candidates[max(range(len(candidates)),key=lambda i:(scores[i],-table.rows[candidates[i]].source_order))]
  else:raise ValueError(route)
  selected.append(chosen);events.append(chosen)
 return predictions,events

def verify_against_original(table,pool,test,pair,domain):
 out=[]
 for route in ('historical_order','uncertainty_diversity','random'):
  seed=SEEDS[domain]+777;pred,sequence=simulate(table,pool,test,pair,route,seed)
  old=sp.seed_indices;sp.seed_indices=lambda table_,pool_,route_,rng_:list(pair)
  try:_,_,original,events=sp.simulate_route(table,'ee_percent',rr.FEATURE,pool,test,route,0,random.Random(seed),set(BUDGETS))
  finally:sp.seed_indices=old
  original=[r for r in original if r['model']=='ridge' and r['n_labeled'] in BUDGETS]
  seq=[r['selected_substrate_id'] for r in events[:max(BUDGETS)]]
  assert seq==[table.rows[i].substrate_id for i in sequence]
  def key(r):return (r['n_labeled'],r['substrate_id'])
  a={key(r):r['predicted_value'] for r in pred};b={key(r):r['predicted_value'] for r in original}
  assert a.keys()==b.keys();maxdiff=max(abs(a[k]-b[k]) for k in a);assert maxdiff<1e-10
  out.append({'domain':domain,'route':route,'budget_predictions':len(a),'selection_prefix_matches':True,'max_abs_prediction_difference':maxdiff})
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--domain',required=True,choices=list(SEEDS));args=ap.parse_args();domain=args.domain
 OUT.mkdir(exist_ok=True);out=OUT/domain;out.mkdir(exist_ok=True);started=time.time()
 table,active=rr.load(domain);design=split_design(table,active,domain)
 audit=set(rr.CONFIG[domain]['audit']);assert not audit&{table.ids[i] for i in active}
 splitrows=[];pairrows=[]
 for i,(test,pool,pairs) in enumerate(design,1):
  splitrows.append({'domain':domain,'split_id':i,'held_out_ids':'|'.join(table.ids[x] for x in test),'candidate_ids':'|'.join(table.ids[x] for x in pool),'n_held_out':len(test),'n_candidate':len(pool)})
  for j,(a,b) in enumerate(pairs,1):pairrows.append({'domain':domain,'split_id':i,'pair_id':j,'substrate_1':table.ids[a],'substrate_2':table.ids[b]})
 rr.output(out/'outer_splits.csv',splitrows);rr.output(out/'initial_pairs.csv',pairrows)
 rr.output(out/'original_function_equivalence.csv',verify_against_original(table,design[0][1],design[0][0],design[0][2][0],domain))
 predictions=[];runs=[];events=[]
 for i,(test,pool,pairs) in enumerate(design,1):
  for j,pair in enumerate(pairs,1):
   for route in ('historical_order','uncertainty_diversity','random'):
    for rep in range(RANDOM_RUNS if route=='random' else 1):
     seed=SEEDS[domain]*10000+i*100+j*10+rep
     preds,selection=simulate(table,pool,test,pair,route,seed)
     bybudget=defaultdict(list)
     for p in preds:
      error=abs(p['observed_value']-p['predicted_value']);bybudget[p['n_labeled']].append(error)
      predictions.append({'domain':domain,'split_id':i,'pair_id':j,'route':route,'random_continuation':rep,'n_labeled':p['n_labeled'],'substrate_id':p['substrate_id'],'observed_ee':p['observed_value'],'predicted_ee':p['predicted_value'],'absolute_error':error})
     means=[statistics.mean(bybudget[n]) for n in BUDGETS];assert all(len(bybudget[n])==len(test) for n in BUDGETS)
     runs.append({'domain':domain,'split_id':i,'pair_id':j,'route':route,'random_continuation':rep,'random_seed':seed,'mean_heldout_mae':statistics.mean(means),**{f'mae_at_{n}':statistics.mean(bybudget[n]) for n in BUDGETS}})
     for step,index in enumerate(selection,1):events.append({'domain':domain,'split_id':i,'pair_id':j,'route':route,'random_continuation':rep,'step':step,'substrate_id':table.ids[index]})
  print(domain,'outer split',i,'/',SPLITS,'elapsed',round(time.time()-started,1),'seconds',flush=True)
 rr.output(out/'predictions.csv',predictions);rr.output(out/'runs.csv',runs);rr.output(out/'selection_events.csv',events)
 byrun=defaultdict(list)
 for r in runs:byrun[(r['split_id'],r['pair_id'],r['route'])].append(r['mean_heldout_mae'])
 split_results=[];pair_results=[]
 for i in range(1,SPLITS+1):
  per=[]
  for j in range(1,PAIRS_PER_SPLIT+1):
   h=statistics.mean(byrun[(i,j,'historical_order')]);u=statistics.mean(byrun[(i,j,'uncertainty_diversity')]);r=statistics.mean(byrun[(i,j,'random')]);item={'domain':domain,'split_id':i,'pair_id':j,'source_mae':h,'ud_mae':u,'random_mae':r,'source_minus_ud':h-u,'random_minus_ud':r-u};pair_results.append(item);per.append(item)
  split_results.append({'domain':domain,'split_id':i,**{key:statistics.mean(x[key] for x in per) for key in ['source_mae','ud_mae','random_mae','source_minus_ud','random_minus_ud']}})
 rr.output(out/'pair_results.csv',pair_results);rr.output(out/'split_results.csv',split_results)
 rng=np.random.default_rng(SEEDS[domain]+500);summary={}
 for key in ('source_minus_ud','random_minus_ud'):
  v=np.array([r[key] for r in split_results]);boot=rng.choice(v,size=(10000,len(v)),replace=True).mean(axis=1)
  summary[key]={'mean':float(v.mean()),'median':float(np.median(v)),'q25_q75':[float(z) for z in np.quantile(v,[.25,.75])],'q025_q975_split_spread':[float(z) for z in np.quantile(v,[.025,.975])],'range':[float(v.min()),float(v.max())],'split_count_favouring_ud':int(np.sum(v>0)),'conditional_split_bootstrap_mean_interval_95':[float(z) for z in np.quantile(boot,[.025,.975])]}
 metadata={'domain':domain,'seed':SEEDS[domain],'n_outer_splits':SPLITS,'test_size':TEST_SIZES[domain],'initial_pairs_per_split':PAIRS_PER_SPLIT,'random_continuations_per_pair':RANDOM_RUNS,'label_budgets':BUDGETS,'metric':'mean Ridge MAE on a fixed common held-out set across five label budgets','existing_locked_cmc_audit_excluded':rr.CONFIG[domain]['audit'],'inputs_sha256':{rr.CONFIG[domain][k]:rr.sha(ROOT/rr.CONFIG[domain][k]) for k in ['records','features','archived']},'original_code_sha256':rr.sha(ROOT/'scripts/scope_progression.py'),'wrapper_sha256':rr.sha(Path(__file__)),'python':sys.version,'numpy':np.__version__,'scikit_learn':rr.sklearn.__version__,'rdkit':rr.rdkit.__version__,'statistics':summary,'elapsed_seconds':time.time()-started,'limitations':'Overlapping random outer splits and shared source datasets; intervals conditional on observed data and split scheme, not independent-dataset or substrate-population inference.'}
 (out/'summary.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2),flush=True)
if __name__=='__main__':main()
