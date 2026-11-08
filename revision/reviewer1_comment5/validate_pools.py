import sys,csv,statistics,collections
from pathlib import Path
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'))
import initial_pair_replay as rr
sp=rr.sp;records=sp.read_jsonl(P/'results/cmcpor_source_corrected_copy.jsonl');rows=sp.load_scope_rows_from_records(records,'cmcpor-fecl');t=sp.build_feature_table(rows,ROOT/rr.CONFIG['cmcpor']['features']);X=t.matrix('rdkit_morgan_stage2p');ids={x:i for i,x in enumerate(t.ids)};y=np.array([float(sp.outcome_value(r.record,'ee_percent')) for r in rows]);locked=set(rr.CONFIG['cmcpor']['audit'])
def read(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))
for mode in ('mixed','sulfonyl'):
 d=P/'results'/mode;splits=read(d/'splits.csv');pred=read(d/'predictions.csv');ev=read(d/'selections.csv');out=read(d/'split_mae.csv');split={(int(r['split_id']),int(r['pair_id'])):r for r in splits};events={(int(r['split_id']),int(r['pair_id']),r['pool'],r['route'],int(r['replicate'])):r for r in ev};groups=collections.defaultdict(list)
 for r in pred:
  s=int(r['split_id']);j=int(r['pair_id']);src=split[(s,j)];ta=set(filter(None,src['test_aryl'].split('|')));ts=set(filter(None,src['test_sulfonyl'].split('|')));assert r['substrate_id'] in (ta if r['test_class']=='aryl' else ts);assert abs(abs(float(r['observed'])-float(r['predicted']))-float(r['abs_error']))<1e-9
  for cl in (r['test_class'],'pooled'):groups[(s,r['pool'],r['route'],cl)].append(float(r['abs_error']))
 for r in out:assert abs(statistics.mean(groups[(int(r['split_id']),r['pool'],r['route'],r['test_class'])])-float(r['mean_mae']))<1e-9
 for k,r in events.items():
  s,j,pool,route,rep=k;src=split[(s,j)];seq=r['selected_ids'].split('|');test=set(filter(None,(src['test_aryl']+'|'+src['test_sulfonyl']).split('|')));assert len(seq)==len(set(seq)) and not set(seq)&(test|locked) and seq[:2]==src['start_ids'].split('|')
  assert sum(x.startswith('6') for x in seq)==int(r['sulfonyl_count'])
  if pool=='aryl_only':assert all(not x.startswith('6') for x in seq)
  if pool=='sulfonyl_only':assert all(x.startswith('6') for x in seq)
  if pool=='mixed' and route=='historical_order':assert seq==events[(s,j,'aryl_only',route,rep)]['selected_ids'].split('|')
 checks=0
 for k,r in events.items():
  s,j,pool,route,rep=k
  if s not in (1,10,20) or j!=1 or rep!=0:continue
  seq=r['selected_ids'].split('|')
  for n in (2,int(len(seq))):
   target=[z for z in pred if int(z['split_id'])==s and int(z['pair_id'])==j and z['pool']==pool and z['route']==route and int(z['replicate'])==rep and int(z['budget'])==n];assert target
   model=make_pipeline(StandardScaler(),Ridge(alpha=10.0,solver='lsqr'));ii=[ids[x] for x in seq[:n]];model.fit(X[ii],y[ii]);pp=np.clip(model.predict(X[[ids[z['substrate_id']] for z in target]]),0,100)
   assert np.allclose(pp,[float(z['predicted']) for z in target],atol=1e-9);checks+=len(target)
 # Check the frozen score's explicit decomposition on the first mixed/single starting state.
 s,j,pool,route,rep=next(k for k in events if k[0]==1 and k[1]==1 and k[3]=='uncertainty_diversity');src=split[(s,j)];test=set(filter(None,(src['test_aryl']+'|'+src['test_sulfonyl']).split('|')));seq=events[(s,j,pool,route,rep)]['selected_ids'].split('|');start=[ids[z] for z in seq[:2]]
 eligible=[i for i,x in enumerate(t.ids) if x not in locked|test and ((pool=='mixed') or (pool=='aryl_only' and not x.startswith('6')) or (pool=='sulfonyl_only' and x.startswith('6'))) and i not in start]
 scores,c=sp.selection_components(t,X,y,start,eligible,'uncertainty_diversity');assert np.allclose(scores,.4*c['diversity_score']+.4*c['uncertainty_score']+.2*c['family_coverage_score']);assert t.ids[eligible[max(range(len(eligible)),key=lambda q:(scores[q],-t.rows[eligible[q]].source_order))]]==seq[2]
 print(mode,'passed',len(pred),'predictions reconciled;',len(events),'sequences checked; independently refitted',checks,'prediction rows; original score and first choice checked')
