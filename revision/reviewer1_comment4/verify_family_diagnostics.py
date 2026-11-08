import csv,statistics,math
from pathlib import Path
p=Path(__file__).resolve().parent; root=p.parents[1]; repo=root/'data/jacs_2025/stage2/reports'
def read(name):
 with (repo/name).open(newline='') as f:return {r['target_substrate_id']:r for r in csv.DictReader(f) if r['model_name']=='elastic_net' and r['target_name']=='ee'}
f1=read('family-heldout-structure-ee-model-predictions.csv');f2=read('family-heldout-structure-pose-ee-model-predictions.csv');t1=read('full-scope-structure-model-predictions.csv');t2=read('full-scope-structure-pose-model-predictions.csv')
for a,b in [(f1,f2),(t1,t2)]:
 assert a.keys()==b.keys() and len(a)==38
 for sid in a:
  x,y=a[sid],b[sid];assert x['split_id']==y['split_id'] and x['family_id']==y['family_id']
  for col in ('train_substrate_ids','validation_substrate_ids'):
   assert set(x[col].split('|'))==set(y[col].split('|'))
  train=set(x['train_substrate_ids'].split('|'));valid=set(x['validation_substrate_ids'].split('|'));assert sid not in train|valid and train.isdisjoint(valid)
with (p/'results/family_results.csv').open() as f:family=list(csv.DictReader(f))
assert len(family)==17 and sum(int(x['n']) for x in family)==38
for x in family:
 ids=[k for k in f1 if f1[k]['family_id']==x['family_id']];assert len(ids)==int(x['n'])
 for data,col in ((f1,'structure_mae'),(f2,'pose_mae')):
  avg=sum(abs(float(data[k]['prediction'])-float(data[k]['observed_target_value'])) for k in ids)/len(ids)
  assert math.isclose(avg,float(x[col]),abs_tol=1e-10)
print('All 38 IDs, model-specific observed values, matched training and validation memberships, and 17 family MAEs independently reconciled; target IDs excluded from training and validation.')
