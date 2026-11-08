#!/usr/bin/env python3
import csv,sys,time,json,hashlib,statistics,random
from pathlib import Path
from collections import defaultdict
import numpy as np
HERE=Path(__file__).resolve().parent.parent/'reviewer1_comment3'
DEST=Path(__file__).resolve().parent/'results'/'corrected_factorial'
sys.path.insert(0,str(HERE.parent/'reviewer1_comment2'))
import weight_sensitivity as ws
sp=ws.sp; rr=ws.rr
for d in ['p7','cmcpor']: rr.CONFIG[d]['features']=str((Path(__file__).resolve().parent/'results'/f'corrected_{d}_stage2p.jsonl').relative_to(rr.ROOT))
B=(2,6,10,15,20)
def read(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))
def write(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
def main(domain):
 start=time.time(); table,active=rr.load(domain); design=ws.load_design(domain,table,active)
 Xs=table.matrix('rdkit_morgan'); Xp=table.matrix('rdkit_morgan_stage2p'); assert np.array_equal(Xs,Xp[:,:Xs.shape[1]]) and Xp.shape[1]-Xs.shape[1]==248
 y=np.array([sp.outcome_value(r.record,'ee_percent') if sp.outcome_value(r.record,'ee_percent') is not None else np.nan for r in table.rows])
 old=Path(__file__).resolve().parent/'results'/'corrected_common_test'/domain
 prior=read(old/'predictions.csv'); events=read(old/'selection_events.csv'); lookup={sid:i for i,sid in enumerate(table.ids)}
 ev=defaultdict(list)
 for r in events:ev[(int(r['split_id']),int(r['pair_id']),r['route'],int(r['random_continuation']))].append((int(r['step']),lookup[r['substrate_id']]))
 out=DEST/domain;out.mkdir(parents=True,exist_ok=True)
 predictions=[]; selections=[]
 for r in prior:
  predictions.append({'domain':domain,'split_id':int(r['split_id']),'pair_id':int(r['pair_id']),'representation':'pose','route':r['route'],'replicate':int(r['random_continuation']),'budget':int(r['n_labeled']),'substrate_id':r['substrate_id'],'observed':float(r['observed_ee']),'predicted':float(r['predicted_ee']),'absolute_error':float(r['absolute_error'])})
 for split,test,pool,pairs in design:
  assert not set(test)&set(pool)
  for pairid,pair in pairs:
   for route,rep in [('historical_order',0),('uncertainty_diversity',0),('random',0),('random',1),('random',2)]:
    seq=list(pair)
    saved=[i for _,i in sorted(ev[(split,pairid,route,rep)])]
    assert seq==saved[:2]
    for n in range(2,21):
     if n in B:
      rows=sp.audit_prediction_rows(table,Xs,y,seq,test,route,rep,'ee_percent',n)
      rows=[x for x in rows if x['model']=='ridge'];assert len(rows)==len(test)
      for x in rows:
       obs=float(x['observed_value']);pred=float(x['predicted_value'])
       predictions.append({'domain':domain,'split_id':split,'pair_id':pairid,'representation':'structure','route':route,'replicate':rep,'budget':n,'substrate_id':x['substrate_id'],'observed':obs,'predicted':pred,'absolute_error':abs(obs-pred)})
     if n==20:break
     if route=='uncertainty_diversity':
      candidates=[i for i in pool if i not in seq]; scores,_=sp.selection_components(table,Xs,y,seq,candidates,route)
      chosen=candidates[max(range(len(candidates)),key=lambda j:(scores[j],-table.rows[candidates[j]].source_order))]
     else:chosen=saved[n]
     seq.append(chosen)
    selections.append({'domain':domain,'split_id':split,'pair_id':pairid,'representation':'structure','route':route,'replicate':rep,'ids':'|'.join(table.ids[i] for i in seq)})
  print(domain,'split',split,'elapsed',round(time.time()-start),flush=True)
 write(out/'predictions.csv',predictions);write(out/'structure_sequences.csv',selections)
 grouped=defaultdict(list)
 for r in predictions:grouped[(r['split_id'],r['pair_id'],r['representation'],r['route'],r['replicate'],r['budget'])].append(r['absolute_error'])
 pair=defaultdict(list)
 for (s,j,feat,route,rep,n),vals in grouped.items():pair[(s,j,feat,route,rep)].append(statistics.mean(vals))
 assert all(len(v)==5 for v in pair.values())
 splitres=[]
 for s in range(1,21):
  a={}
  for feat in ('structure','pose'):
   for route in ('historical_order','uncertainty_diversity','random'):
    vals=[statistics.mean(pair[(s,j,feat,route,rep)]) for j in (1,2,3) for rep in (range(3) if route=='random' else [0])]
    a[feat+'_'+route]=statistics.mean(vals)
  ss=a['structure_historical_order'];su=a['structure_uncertainty_diversity'];ps=a['pose_historical_order'];pu=a['pose_uncertainty_diversity']
  a.update({'ordering_benefit_structure':ss-su,'ordering_benefit_pose':ps-pu,'interaction_structure_minus_pose':(ss-su)-(ps-pu),'combined_vs_structure_baseline':ss-pu,'combined_vs_structure_acquire':su-pu,'combined_vs_pose_source':ps-pu,'random_benefit_structure':a['structure_random']-su,'random_benefit_pose':a['pose_random']-pu})
  splitres.append({'domain':domain,'split_id':s,**a})
 write(out/'split_results.csv',splitres)
 summary={}
 for key in splitres[0]:
  if key in ('domain','split_id'):continue
  x=np.array([r[key] for r in splitres]);summary[key]={'mean':float(x.mean()),'median':float(np.median(x)),'iqr':[float(z) for z in np.quantile(x,[.25,.75])],'positive_splits':int(np.sum(x>1e-10)),'negative_splits':int(np.sum(x< -1e-10))}
 meta={'domain':domain,'features':{'structure':list(Xs.shape),'pose':list(Xp.shape)},'budgets':B,'splits':20,'pairs':3,'random_replicates':3,'summaries':summary,'note':'Pose predictions and sequences reuse R1.1 validated common-test records; all results conditional on overlapping splits of fixed datasets.','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main(sys.argv[1])
