import os,sys,csv,statistics,json,random
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'));import initial_pair_replay as rr
for d in ['p7','cmcpor']:rr.CONFIG[d]['features']=str((P/'results'/f'corrected_{d}_stage2p.jsonl').relative_to(ROOT))
summary=[];curves=[]
for d in ['p7','cmcpor']:
 t,p=rr.load(d)
 for route in ['historical_order','uncertainty_diversity','diversity_first','performance_first','random']:
  vals=[]
  for rep in range(3 if route=='random' else 1):
   c,e=rr.replay(t,p,route,rep,rr.SEED+rep);v=statistics.mean(x['mae'] for x in c);vals.append(v)
   for row in c:curves.append({'domain':d,'route':route,'replicate':rep,'n_labeled':row['n_labeled'],'mae':row['mae']})
  summary.append({'domain':d,'route':route,'mean_prefix_mae':statistics.mean(vals),'replicates':len(vals)})
  print(d,route,summary[-1]['mean_prefix_mae'],flush=True)
for filename,rows in [('corrected_original_routes.csv',summary),('corrected_original_curves.csv',curves)]:
 with (P/'results'/filename).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
