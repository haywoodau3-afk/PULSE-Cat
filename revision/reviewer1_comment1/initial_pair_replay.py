#!/usr/bin/env python3
"""Reproduce archived ee curves and evaluate common starting pairs.

Uses the original scope progression functions with a scoped starting-pair
override. No original data or code is changed. Run from the project root.
"""
import argparse, csv, hashlib, itertools, json, os, random, statistics, sys, time
from collections import defaultdict
from pathlib import Path
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import sklearn, rdkit
from scripts import scope_progression as sp

DEST=Path(__file__).resolve().parent/'results'
FEATURE='rdkit_morgan_stage2p'
SEED=20261105
CONFIG={
 'p7': {'catalyst':'fe-p7-cl','records':'data/jacs_2025/stage2/curated-reaction-records.jsonl','features':'data/jacs_2025/stage2/features/stage2p-features.jsonl','archived':'data/jacs_2025/scope_progression/learning-curve.csv','exclude':['1ad'],'audit':[],'family':None,'expected':38},
 'cmcpor': {'catalyst':'cmcpor-fecl','records':'data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl','features':'data/expansion/catalyst_rerun/cmcpor_uff_full/stage2p/features/stage2p-features.jsonl','archived':'data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/learning-curve.csv','exclude':[],'audit':['2y','2z','4a','4b','4c','4d','4e'],'family':'angew-aryl-c-h-amination','expected':26},
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(domain):
 c=CONFIG[domain]; rows=sp.load_scope_rows(ROOT/c['records'],c['catalyst'])
 rows=[r for r in rows if r.substrate_id not in c['exclude'] and (not c['family'] or r.family_id==c['family'])]
 table=sp.build_feature_table(rows,ROOT/c['features'])
 pool=[i for i,r in enumerate(rows) if r.substrate_id not in c['audit'] and sp.outcome_value(r.record,'ee_percent') is not None]
 assert len(pool)==c['expected'],(domain,len(pool),c['expected'])
 assert all(a in table.ids for a in c['audit'])
 return table,pool
def rows_csv(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))
def output(path,rows):
 if not rows:return
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def replay(table,pool,route,replicate,seed,pair=None):
 old=sp.seed_indices
 if pair is not None:
  assert len(set(pair))==2 and all(i in pool for i in pair)
  sp.seed_indices=lambda t,p,r,rng:list(pair)
 try:
  curves,_,_,events=sp.simulate_route(table,'ee_percent',FEATURE,pool,[],route,replicate,random.Random(seed),set())
 finally:sp.seed_indices=old
 ridge=[r for r in curves if r['model']=='ridge' and r['evaluation_pool']=='remaining_active']
 assert [r['n_labeled'] for r in ridge]==list(range(2,len(pool)))
 return ridge,events
def original_check(domain,table,pool):
 archive=rows_csv(ROOT/CONFIG[domain]['archived']);result=[]
 event_path=(ROOT/CONFIG[domain]['archived']).parent/'selection-events.csv'
 archived_events=rows_csv(event_path)
 for route in ['historical_order','uncertainty_diversity']:
  cur,events=replay(table,pool,route,0,SEED)
  old={int(r['n_labeled']):float(r['mae']) for r in archive if r['route']==route and r['replicate']=='0' and r['target']=='ee_percent' and r['model']=='ridge' and r['evaluation_pool']=='remaining_active' and r['mae']}
  diffs=[abs(float(r['mae'])-old[r['n_labeled']]) for r in cur]
  original=[r['selected_substrate_id'] for r in archived_events if r['route']==route and r['replicate']=='0' and r['target']=='ee_percent']
  replayed=[r['selected_substrate_id'] for r in events]
  result.append({'domain':domain,'route':route,'n_prefixes':len(cur),'archived_mean_mae':statistics.mean(old.values()),'replay_mean_mae':statistics.mean(r['mae'] for r in cur),'max_absolute_mae_difference':max(diffs),'replay_initial_pair':','.join(replayed[:2]),'selection_sequence_matches_archive':original==replayed,'archived_selection_count':len(original),'replay_selection_count':len(replayed)})
 return result
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['reproduce','main'],required=True);parser.add_argument('--domain',choices=list(CONFIG),required=True);parser.add_argument('--pairs',type=int,default=50);parser.add_argument('--random-continuations',type=int,default=3);args=parser.parse_args()
 DEST.mkdir(exist_ok=True);table,pool=load(args.domain);out=DEST/args.domain;out.mkdir(exist_ok=True)
 if args.phase=='reproduce':
  result=original_check(args.domain,table,pool);output(out/'reproduction_check.csv',result);print(json.dumps(result,indent=2),flush=True);return
 started=time.time();comb=list(itertools.combinations(pool,2));prng=random.Random(SEED+(0 if args.domain=='p7' else 1));pairs=prng.sample(comb,args.pairs)
 plan=[{'pair_id':i+1,'substrate_1':table.rows[a].substrate_id,'substrate_2':table.rows[b].substrate_id} for i,(a,b) in enumerate(pairs)]
 output(out/'initial_pairs.csv',plan)
 pairrows=[];curve_rows=[]
 for i,pair in enumerate(pairs):
  scores={}
  for route in ['historical_order','uncertainty_diversity','random']:
   means=[]
   for rep in range(args.random_continuations if route=='random' else 1):
    rseed=SEED+1000000*(0 if args.domain=='p7' else 1)+(i+1)*100+rep
    curve,_=replay(table,pool,route,rep,rseed,pair)
    means.append(statistics.mean(r['mae'] for r in curve))
    for row in curve:curve_rows.append({'domain':args.domain,'pair_id':i+1,'substrate_1':plan[i]['substrate_1'],'substrate_2':plan[i]['substrate_2'],'route':route,'continuation':rep,'random_seed':rseed,'n_labeled':row['n_labeled'],'n_evaluated':row['n_evaluated'],'mae':row['mae']})
   scores[route]=statistics.mean(means)
  h,u,r=scores['historical_order'],scores['uncertainty_diversity'],scores['random']
  pairrows.append({'domain':args.domain,**plan[i],'reported_order_mae':h,'uncertainty_diversity_mae':u,'random_mean_mae':r,'reported_minus_ud':h-u,'random_minus_ud':r-u,'relative_reduction_vs_reported_pct':100*(h-u)/h if h else None})
  print(args.domain,'pair',i+1,'/',args.pairs,'elapsed',round(time.time()-started,1),'seconds',flush=True)
 output(out/'pair_results.csv',pairrows);output(out/'learning_curves.csv',curve_rows)
 rng=np.random.default_rng(SEED+(100 if args.domain=='p7' else 101));boot={}
 for field in ['reported_minus_ud','random_minus_ud']:
  vals=np.array([r[field] for r in pairrows]);sample=rng.choice(vals,size=(10000,len(vals)),replace=True).mean(axis=1)
  boot[field]={'mean':float(np.mean(vals)),'median':float(np.median(vals)),'q025':float(np.quantile(vals,.025)),'q975':float(np.quantile(vals,.975)),'fraction_positive':float(np.mean(vals>0)),'mean_bootstrap_ci_95':[float(x) for x in np.quantile(sample,[.025,.975])]}
 metadata={'domain':args.domain,'n_pairs':len(pairs),'random_continuations_per_pair':args.random_continuations,'selection_seed':SEED+(0 if args.domain=='p7' else 1),'feature_set':FEATURE,'score':'mean Ridge MAE over remaining active pool at all nonempty prefixes 2..N-1','inputs_sha256':{CONFIG[args.domain][k]:sha(ROOT/CONFIG[args.domain][k]) for k in ['records','features','archived']},'code_sha256':sha(ROOT/'scripts/scope_progression.py'),'wrapper_sha256':sha(Path(__file__)),'python':sys.version,'numpy':np.__version__,'scikit_learn':sklearn.__version__,'rdkit':rdkit.__version__,'statistics':boot,'elapsed_seconds':time.time()-started}
 (out/'summary.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2),flush=True)
if __name__=='__main__':main()
