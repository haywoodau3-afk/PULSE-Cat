#!/usr/bin/env python3
import sys,os,random,itertools,csv,json,statistics,hashlib,time
from pathlib import Path
from collections import defaultdict
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'))
import initial_pair_replay as rr
import numpy as np
rr.CONFIG['cmcpor']['features']=str((HERE/'results/corrected_cmcpor_stage2p.jsonl').relative_to(ROOT));sp=rr.sp; seeds={'mixed':20261112,'sulfonyl':20261113}; locked=set(rr.CONFIG['cmcpor']['audit']);B={'mixed':(2,6,10,15,20),'sulfonyl':(2,6,10,13)}
def write(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
def main(mode):
 st=time.time(); records=sp.read_jsonl(ROOT/'revision/reviewer1_comment5/results/cmcpor_source_corrected_copy.jsonl');rows=sp.load_scope_rows_from_records(records,'cmcpor-fecl');table=sp.build_feature_table(rows,ROOT/rr.CONFIG['cmcpor']['features']); X=table.matrix('rdkit_morgan_stage2p');y=np.array([sp.outcome_value(x.record,'ee_percent') if sp.outcome_value(x.record,'ee_percent') is not None else np.nan for x in table.rows]);classes=['sulfonyl' if 'sulfonyl' in x.family_id else 'aryl' for x in rows];aryl=[i for i in range(len(rows)) if classes[i]=='aryl' and table.ids[i] not in locked];sulf=[i for i in range(len(rows)) if classes[i]=='sulfonyl'];assert len(aryl)==26 and len(sulf)==17 and not set(table.ids[i] for i in aryl+sulf)&locked
 rng=random.Random(seeds[mode]);seen=set();design=[]
 while len(design)<20:
  if mode=='mixed':test_a=sorted(rng.sample(aryl,3));test_s=sorted(rng.sample(sulf,2));startpool=[i for i in aryl if i not in test_a]
  else:test_a=[];test_s=sorted(rng.sample(sulf,3));startpool=[i for i in sulf if i not in test_s]
  key=tuple(test_a+test_s)
  if key in seen:continue
  seen.add(key);pairs=rng.sample(list(itertools.combinations(startpool,2)),3)
  design.append((test_a,test_s,pairs))
 preds=[];runs=[];events=[];splitrows=[]
 for s,(ta,ts,pairs) in enumerate(design,1):
  testa=ta;tests=ts;test=ta+ts;pa=[i for i in aryl if i not in test];ps=[i for i in sulf if i not in test];pools={'aryl_only':pa,'mixed':pa+ps} if mode=='mixed' else {'sulfonyl_only':ps}
  for j,pair in enumerate(pairs,1):
   splitrows.append({'mode':mode,'split_id':s,'pair_id':j,'test_aryl':'|'.join(table.ids[i] for i in ta),'test_sulfonyl':'|'.join(table.ids[i] for i in ts),'start_ids':'|'.join(table.ids[i] for i in pair)})
   for name,pool in pools.items():
    assert set(pair)<=set(pool) and not set(pool)&set(test) and not set(table.ids[i] for i in pool+test)&locked
    for route,rep in [('historical_order',0),('uncertainty_diversity',0),('random',0),('random',1),('random',2)]:
     randomseed=seeds[mode]*10000+s*100+j*10+rep; rrng=random.Random(randomseed);selected=list(pair)
     for n in range(2,max(B[mode])+1):
      if n in B[mode]:
       r=sp.audit_prediction_rows(table,X,y,selected,test,route,rep,'ee_percent',n);q=[x for x in r if x['model']=='ridge'];assert len(q)==len(test)
       for x in q:
        i=table.ids.index(x['substrate_id']);obs=float(x['observed_value']);pred=float(x['predicted_value']);preds.append({'mode':mode,'split_id':s,'pair_id':j,'pool':name,'route':route,'replicate':rep,'budget':n,'test_class':classes[i],'substrate_id':table.ids[i],'observed':obs,'predicted':pred,'abs_error':abs(obs-pred)})
      if n==max(B[mode]):break
      candidate=[i for i in pool if i not in selected]
      if route=='historical_order':chosen=min(candidate,key=lambda i:table.rows[i].source_order)
      elif route=='random':chosen=candidate[rrng.randrange(len(candidate))]
      else:
       scores,_=sp.selection_components(table,X,y,selected,candidate,route);chosen=candidate[max(range(len(candidate)),key=lambda k:(scores[k],-table.rows[candidate[k]].source_order))]
      selected.append(chosen)
     events.append({'mode':mode,'split_id':s,'pair_id':j,'pool':name,'route':route,'replicate':rep,'random_seed':randomseed,'selected_ids':'|'.join(table.ids[i] for i in selected),'sulfonyl_count':sum(classes[i]=='sulfonyl' for i in selected)})
  print(mode,'split',s,'elapsed',round(time.time()-st,1),flush=True)
 out=HERE/'results'/'corrected_class'/mode;out.mkdir(parents=True,exist_ok=True);write(out/'splits.csv',splitrows);write(out/'predictions.csv',preds);write(out/'selections.csv',events)
 # Every test class has constant size within mode, so this mean matches the prescribed average of per-budget MAEs.
 g=defaultdict(list)
 for x in preds:
  key=(x['split_id'],x['pool'],x['route'],x['test_class']);g[key].append(x['abs_error']);g[(x['split_id'],x['pool'],x['route'],'pooled')].append(x['abs_error'])
 summaryrows=[]
 for key,vals in sorted(g.items()):
  s,pool,route,cls=key;expected=3*(3 if route=='random' else 1)*len(B[mode])*(len(design[s-1][0]) if cls=='aryl' else len(design[s-1][1]) if cls=='sulfonyl' else len(design[s-1][0])+len(design[s-1][1]));assert len(vals)==expected
  summaryrows.append({'mode':mode,'split_id':s,'pool':pool,'route':route,'test_class':cls,'mean_mae':statistics.mean(vals)})
 write(out/'split_mae.csv',summaryrows)
 grouped=defaultdict(list)
 for x in summaryrows:grouped[(x['pool'],x['route'],x['test_class'])].append(x['mean_mae'])
 agg=[]
 for (pool,route,cls),vals in sorted(grouped.items()):
  assert len(vals)==20;agg.append({'mode':mode,'pool':pool,'route':route,'test_class':cls,'mean_mae':statistics.mean(vals),'median_mae':statistics.median(vals),'q25':float(np.quantile(vals,.25)),'q75':float(np.quantile(vals,.75))})
 write(out/'summary.csv',agg)
 lookup={(r['split_id'],r['pool'],r['route'],r['test_class']):r['mean_mae'] for r in summaryrows}; contrasts=[]
 for pool in (['aryl_only','mixed'] if mode=='mixed' else ['sulfonyl_only']):
  for cls in (['aryl','sulfonyl','pooled'] if mode=='mixed' else ['sulfonyl']):
   for comp in ('historical_order','random'):
    ds=[lookup[(s,pool,comp,cls)]-lookup[(s,pool,'uncertainty_diversity',cls)] for s in range(1,21)];contrasts.append({'comparison':'policy','pool':pool,'test_class':cls,'contrast':comp+' minus uncertainty_diversity','mean_difference':statistics.mean(ds),'median_difference':statistics.median(ds),'q25':float(np.quantile(ds,.25)),'q75':float(np.quantile(ds,.75)),'positive_splits':sum(x>1e-10 for x in ds),'negative_splits':sum(x< -1e-10 for x in ds)})
 if mode=='mixed':
  for cls in ('aryl','sulfonyl','pooled'):
   for route in ('historical_order','uncertainty_diversity','random'):
    ds=[lookup[(s,'aryl_only',route,cls)]-lookup[(s,'mixed',route,cls)] for s in range(1,21)];contrasts.append({'comparison':'pool','pool':'aryl_only vs mixed','test_class':cls,'contrast':'aryl_only minus mixed '+route,'mean_difference':statistics.mean(ds),'median_difference':statistics.median(ds),'q25':float(np.quantile(ds,.25)),'q75':float(np.quantile(ds,.75)),'positive_splits':sum(x>1e-10 for x in ds),'negative_splits':sum(x< -1e-10 for x in ds)})
 write(out/'contrasts.csv',contrasts)
 meta={'mode':mode,'seed':seeds[mode],'budget':B[mode],'n_splits':20,'n_pairs':3,'random_replicates':3,'locked_audit':sorted(locked),'n_predictions':len(preds),'n_trajectories':len(events),'input_hash':hashlib.sha256((ROOT/'revision/reviewer1_comment5/results/cmcpor_source_corrected_copy.jsonl').read_bytes()).hexdigest(),'code_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'note':'Conditional descriptive retrospective analysis; original curated source order, class-stratified overlapping holdouts, unknown to model reaction conditions.'}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print('completed',mode,'seconds',round(time.time()-st,2),flush=True)
if __name__=='__main__':main(sys.argv[1])
