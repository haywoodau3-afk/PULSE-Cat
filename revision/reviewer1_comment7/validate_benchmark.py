import os,sys,csv,json,math,statistics
from pathlib import Path
from collections import defaultdict
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'));import initial_pair_replay as rr
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scipy.special import ndtr

def read(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
for domain in ('p7','cmcpor'):
 old=ROOT/'revision/reviewer1_comment1/results/common_test'/domain;out=P/'results'/domain;table,active=rr.load(domain);ids=table.ids;idx={v:i for i,v in enumerate(ids)};X=table.matrix(rr.FEATURE);K=table.similarity_matrix;y=np.array([rr.sp.outcome_value(r.record,'ee_percent') if rr.sp.outcome_value(r.record,'ee_percent') is not None else np.nan for r in table.rows]);splits={int(x['split_id']):x for x in read(old/'outer_splits.csv')};pairs={(int(x['split_id']),int(x['pair_id'])):[x['substrate_1'],x['substrate_2']] for x in read(old/'initial_pairs.csv')};events=read(out/'selections.csv');pred=read(out/'predictions.csv');scores=read(out/'selected_scores.csv');grp=defaultdict(list)
 for p in pred:
  assert abs(float(p['abs_error'])-abs(float(p['observed'])-float(p['predicted'])))<1e-9;grp[(int(p['split_id']),int(p['pair_id']),p['route'],int(p['replicate']),int(p['budget']))].append(p)
 records={(int(r['split_id']),int(r['pair_id']),r['route'],int(r['replicate'])):r for r in events};firstscores={(int(r['split_id']),int(r['pair_id']),r['route'],int(r['replicate'])):r for r in scores if int(r['n_labeled'])==2};refits=0;first=0
 for key,r in records.items():
  s,j,route,rep=key;seq=r['selected_ids'].split('|');test=splits[s]['held_out_ids'].split('|');pool=splits[s]['candidate_ids'].split('|');assert len(seq)==len(set(seq))==20 and not set(seq)&set(test) and set(seq)<=set(pool) and seq[:2]==pairs[s,j]
  for n in [2,6,10,15,20]:assert abs(float(r['best_'+str(n)])-max(y[idx[x]] for x in seq[:n]))<1e-10
  if s<=2:
   for n in [2,6,10,15,20]:
    p=grp[s,j,route,rep,n];train=[idx[x] for x in seq[:n]];ti=[idx[x['substrate_id']] for x in p];model=make_pipeline(StandardScaler(),Ridge(alpha=10.,solver='lsqr'));model.fit(X[train],y[train]);z=np.clip(model.predict(X[ti]),0,100);assert np.max(np.abs(z-np.array([float(x['predicted']) for x in p])))<1e-8;refits+=len(p)
   train=[idx[x] for x in seq[:2]];cand=[idx[x] for x in pool if x not in seq[:2]]
   # Restore source table order: the saved candidate list is already table order.
   if route=='qbc':
    pp=rr.sp.fit_predict_models(X,table.fingerprint_matrix,train,cand,y);val=np.std(np.array([pp['ridge'],pp['elastic_net'],pp['tanimoto_knn']]),axis=0)
   else:
    yt=y[train];center=float(np.mean(yt));scale=float(np.std(yt));scale=scale if scale>1e-12 else 1.;A=K[np.ix_(train,train)]+.05*np.eye(len(train));cross=K[np.ix_(cand,train)];mu=center+cross@np.linalg.solve(A,yt-center);cov=scale**2*(K[np.ix_(cand,cand)]-cross@np.linalg.solve(A,cross.T));cov=(cov+cov.T)/2
    if route=='expected_improvement':
     sd=np.sqrt(np.maximum(np.diag(cov),0));delta=mu-max(yt);z=np.divide(delta,sd,out=np.zeros_like(sd),where=sd>1e-12);val=np.where(sd>1e-12,delta*ndtr(z)+sd*np.exp(-z*z/2)/math.sqrt(2*math.pi),np.maximum(delta,0))
    else:
     eig=np.linalg.eigvalsh(cov);jitter=max(1e-9,-float(eig.min())+1e-9);rng=np.random.default_rng(int(r['seed']));val=mu+np.linalg.cholesky(cov+jitter*np.eye(len(cand)))@rng.standard_normal(len(cand))
   k=max(range(len(cand)),key=lambda k:(val[k],-table.rows[cand[k]].source_order));assert ids[cand[k]]==seq[2] and abs(float(firstscores[key]['score'])-float(val[k]))<1e-7;first+=1
 # Check each split aggregation, averaging stochastic replicates equally and each budget equally.
 for r in read(out/'split_results.csv'):
  route=r['route'];s=int(r['split_id'])
  if route not in ('qbc','expected_improvement','thompson'):continue
  ms=[statistics.mean(float(x['abs_error']) for x in pred if int(x['split_id'])==s and x['route']==route and int(x['budget'])==n) for n in [2,6,10,15,20]];assert abs(statistics.mean(ms)-float(r['mean_heldout_mae']))<1e-9
 print(json.dumps({'domain':domain,'trajectories_checked':len(events),'prediction_errors_checked':len(pred),'independent_ridge_prediction_refits':refits,'first_decisions_independently_checked':first,'gp_verification':'independent linear solve for mean and covariance, analytic EI and seeded correlated Thompson draw','audit_and_test_exclusion':'passed'}))
