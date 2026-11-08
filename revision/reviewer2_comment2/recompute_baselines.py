#!/usr/bin/env python3
import os,sys,csv,json,random,statistics,time,hashlib
from pathlib import Path
from collections import defaultdict
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'))
import initial_pair_replay as rr
import numpy as np
from scipy.stats import norm
from scipy.linalg import cho_factor,cho_solve
sp=rr.sp;
for d in ['p7','cmcpor']:rr.CONFIG[d]['features']=str((P/'results'/f'corrected_{d}_stage2p.jsonl').relative_to(ROOT))
B=(2,6,10,15,20);SEED={'p7':20261108,'cmcpor':20261109};NOISE=.05

def read(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 assert rows
 with open(p,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
def posterior(K,y,train,candidates):
 vals=y[train];center=float(np.mean(vals));scale=float(np.std(vals));scale=scale if scale>1e-12 else 1.;A=K[np.ix_(train,train)]+NOISE*np.eye(len(train));cross=K[np.ix_(candidates,train)];C=K[np.ix_(candidates,candidates)];cf=cho_factor(A,lower=True,check_finite=True);mean=center+scale*(cross@cho_solve(cf,(vals-center)/scale));cov=scale**2*(C-cross@cho_solve(cf,cross.T));cov=(cov+cov.T)/2;return mean,cov

def main(domain):
 st=time.time();old=P/'results'/'corrected_common_test'/domain;out=P/'results'/'corrected_baselines'/domain;out.mkdir(parents=True,exist_ok=True);table,active=rr.load(domain);ids=table.ids;idx={x:i for i,x in enumerate(ids)};X=table.matrix(rr.FEATURE);K=table.similarity_matrix;y=np.array([sp.outcome_value(r.record,'ee_percent') if sp.outcome_value(r.record,'ee_percent') is not None else np.nan for r in table.rows]);splits=read(old/'outer_splits.csv');pairs=read(old/'initial_pairs.csv');pred=[];events=[];score_rows=[]
 for r in splits:
  s=int(r['split_id']);test=[idx[x] for x in r['held_out_ids'].split('|')];pool=[idx[x] for x in r['candidate_ids'].split('|')];assert set(test).isdisjoint(pool) and set(test+pool)==set(active)
  for pr in [x for x in pairs if int(x['split_id'])==s]:
   j=int(pr['pair_id']);pair=[idx[pr['substrate_1']],idx[pr['substrate_2']]]
   for route,rep in [('qbc',0),('expected_improvement',0),('thompson',0),('thompson',1),('thompson',2)]:
    seed=SEED[domain]*10000+s*100+j*10+rep+5000000;rng=np.random.default_rng(seed);selected=list(pair);best={}
    for n in range(2,21):
     if n in B:
      model=sp.fit_ridge(X[selected],y[selected]);model.fit(X[selected],y[selected]);yp=np.clip(model.predict(X[test]),0,100);best[str(n)]=float(np.max(y[selected]))
      for i,v in zip(test,yp):pred.append({'domain':domain,'split_id':s,'pair_id':j,'route':route,'replicate':rep,'budget':n,'substrate_id':ids[i],'observed':float(y[i]),'predicted':float(v),'abs_error':abs(float(y[i]-v))})
     if n==20:break
     cand=[i for i in pool if i not in selected]
     if route=='qbc':
      pp=sp.fit_predict_models(X,table.fingerprint_matrix,selected,cand,y);val=np.std(np.vstack([pp[x] for x in ['ridge','elastic_net','tanimoto_knn']]),axis=0)
     else:
      mu,cov=posterior(K,y,selected,cand)
      if route=='expected_improvement':
       sd=np.sqrt(np.maximum(np.diag(cov),0));improvement=mu-max(y[selected]);z=np.divide(improvement,sd,out=np.zeros_like(sd),where=sd>1e-12);val=np.where(sd>1e-12,improvement*norm.cdf(z)+sd*norm.pdf(z),np.maximum(improvement,0))
      else:
       eig=np.linalg.eigvalsh(cov);jitter=max(1e-9,-float(eig.min())+1e-9);val=mu+np.linalg.cholesky(cov+jitter*np.eye(len(cand)))@rng.standard_normal(len(cand))
     k=max(range(len(cand)),key=lambda z:(val[z],-table.rows[cand[z]].source_order));chosen=cand[k];score_rows.append({'domain':domain,'split_id':s,'pair_id':j,'route':route,'replicate':rep,'n_labeled':n,'selected_id':ids[chosen],'score':float(val[k])});selected.append(chosen)
    events.append({'domain':domain,'split_id':s,'pair_id':j,'route':route,'replicate':rep,'seed':seed,'selected_ids':'|'.join(ids[i] for i in selected),**{'best_'+n:v for n,v in best.items()}})
  print(domain,'split',s,'seconds',round(time.time()-st,1),flush=True)
 write(out/'predictions.csv',pred);write(out/'selections.csv',events);write(out/'selected_scores.csv',score_rows)
 # Reuse earlier comparison paths and held-out prediction scores, never using their unseen outcomes for selection.
 prev=read(old/'predictions.csv');prev_events=read(old/'selection_events.csv');g=defaultdict(list)
 for r in pred:g[(r['split_id'],r['route'],r['budget'])].append(r['abs_error'])
 for r in prev:g[(int(r['split_id']),r['route'],int(r['n_labeled']))].append(float(r['absolute_error']))
 bg=defaultdict(list)
 for r in events:
  for n in B:bg[(r['split_id'],r['route'],n)].append(r['best_'+str(n)])
 paths=defaultdict(list)
 for r in prev_events:paths[(int(r['split_id']),int(r['pair_id']),r['route'],int(r['random_continuation']))].append((int(r['step']),r['substrate_id']))
 for (s,j,route,rep),v in paths.items():
  seq=[idx[x] for _,x in sorted(v)];assert len(seq)>=20
  for n in B:bg[(s,route,n)].append(float(np.max(y[seq[:n]])))
 routes=('historical_order','uncertainty_diversity','random','qbc','expected_improvement','thompson');split=[]
 for s in range(1,21):
  for route in routes:
   maes=[statistics.mean(g[s,route,n]) for n in B];bests=[statistics.mean(bg[s,route,n]) for n in B];split.append({'domain':domain,'split_id':s,'route':route,'mean_heldout_mae':statistics.mean(maes),**{f'mae_{n}':v for n,v in zip(B,maes)},**{f'best_{n}':v for n,v in zip(B,bests)}})
 write(out/'split_results.csv',split);lookup={(r['split_id'],r['route']):r for r in split};summary=[]
 for route in routes:
  rs=[lookup[s,route] for s in range(1,21)];ds=[lookup[s,route]['mean_heldout_mae']-lookup[s,'uncertainty_diversity']['mean_heldout_mae'] for s in range(1,21)];summary.append({'domain':domain,'route':route,'mean_mae':statistics.mean(r['mean_heldout_mae'] for r in rs),'comparator_minus_pulse':statistics.mean(ds),'median_comparator_minus_pulse':statistics.median(ds),'splits_favour_pulse':sum(x>1e-10 for x in ds),'splits_favour_comparator':sum(x< -1e-10 for x in ds),**{f'mean_best_{n}':statistics.mean(r[f'best_{n}'] for r in rs) for n in B},**{f'mean_mae_{n}':statistics.mean(r[f'mae_{n}'] for r in rs) for n in B}})
 write(out/'summary.csv',summary)
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 inputs={str(x.relative_to(ROOT)):sha(x) for x in [ROOT/rr.CONFIG[domain]['records'],ROOT/rr.CONFIG[domain]['features'],old/'outer_splits.csv',old/'initial_pairs.csv',old/'predictions.csv',old/'selection_events.csv',ROOT/'scripts/scope_progression.py',Path(__file__)]}
 meta={'domain':domain,'seed':SEED[domain],'n_splits':20,'starts_per_split':3,'ts_replicates':3,'budgets':B,'gp_kernel':'Morgan fingerprint Tanimoto','gp_noise_variance_standardised':NOISE,'gp_outcome_scale':'revealed-label mean and population sd; scale=1 if sd=0','ei_incumbent':'best revealed |ee|, zero exploration offset','ts':'joint latent GP posterior sample, stable Cholesky with eigenvalue-derived jitter','input_sha256':inputs,'python':sys.version,'numpy':np.__version__,'rdkit':rr.rdkit.__version__,'sklearn':rr.sklearn.__version__,'elapsed_seconds':time.time()-st}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
if __name__=='__main__':main(sys.argv[1])
