#!/usr/bin/env python3
import csv,json,hashlib,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent; IN=ROOT/'data/jacs_2025/stage2/reports'; OUT=HERE/'results';OUT.mkdir(exist_ok=True)
files={'family_structure':'family-heldout-structure-ee-model-predictions.csv','family_pose':'family-heldout-structure-pose-ee-model-predictions.csv','target_structure':'full-scope-structure-model-predictions.csv','target_pose':'full-scope-structure-pose-model-predictions.csv','splits':'family-heldout-ee-splits.json'}
def read(key):
 with (IN/files[key]).open(newline='') as f:r=[x for x in csv.DictReader(f) if x['model_name']=='elastic_net' and x['target_name']=='ee']
 assert len(r)==38 and len({x['target_substrate_id'] for x in r})==38
 return {x['target_substrate_id']:x for x in r}
def write(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
sets={k:read(k) for k in files if k!='splits'}; ids=set(sets['family_structure']); assert all(set(x)==ids for x in sets.values())
js=json.loads((IN/files['splits']).read_text());splitmap={x['heldout_family_id']:x for x in js['splits']}; family_of={k:v['family_id'] for k,v in sets['family_structure'].items()}; rows=[]
for sid in sorted(ids):
 a=sets['family_structure'][sid];b=sets['family_pose'][sid]; ta=sets['target_structure'][sid];tb=sets['target_pose'][sid];family=a['family_id'];assert family==a['heldout_family_id']==b['family_id']==b['heldout_family_id'];assert all(abs(float(x['observed_target_value'])-float(a['observed_target_value']))<1e-9 for x in (b,ta,tb))
 for x in (a,b):
  assert x['split_mode']=='family_holdout' and x['split_id']==family
  assert not ({sid}|{i for i,f in family_of.items() if f==family}) & set(x['train_substrate_ids'].split('|'))
  assert not ({sid}|{i for i,f in family_of.items() if f==family}) & set(x['validation_substrate_ids'].split('|'))
  assert set(x['train_substrate_ids'].split('|'))==set(splitmap[family]['train_substrate_ids']) and set(x['validation_substrate_ids'].split('|'))==set(splitmap[family]['validation_substrate_ids'])
 for x in (a,b,ta,tb): assert abs(abs(float(x['observed_target_value'])-float(x['prediction']))-float(x['abs_error']))<1e-9
 ea=abs(float(a['observed_target_value'])-float(a['prediction'])); eb=abs(float(b['observed_target_value'])-float(b['prediction']))
 rows.append({'substrate_id':sid,'family_id':family,'observed_ee':float(a['observed_target_value']),'structure_prediction':float(a['prediction']),'pose_prediction':float(b['prediction']),'structure_abs_error':ea,'pose_abs_error':eb,'difference_structure_minus_pose':ea-eb})
for key,target in [('target_structure',12.612),('target_pose',8.583),('family_structure',10.406),('family_pose',9.334)]:
 m=statistics.mean(abs(float(r['observed_target_value'])-float(r['prediction'])) for r in sets[key].values());assert abs(m-target)<.00051,(key,m,target);print(key,m)
g=defaultdict(list)
for r in rows:g[r['family_id']].append(r)
families=[]
for f,items in sorted(g.items()):
 a=statistics.mean(r['structure_abs_error'] for r in items);b=statistics.mean(r['pose_abs_error'] for r in items)
 families.append({'family_id':f,'n':len(items),'substrate_ids':'|'.join(r['substrate_id'] for r in items),'structure_mae':a,'pose_mae':b,'difference_structure_minus_pose':a-b,'sum_error_difference':sum(r['difference_structure_minus_pose'] for r in items)})
assert len(g)==17;largest=max(families,key=lambda r:r['n']);other=[r for r in rows if r['family_id']!=largest['family_id']];balanced_a=statistics.mean(r['structure_mae'] for r in families);balanced_b=statistics.mean(r['pose_mae'] for r in families)
summary={'n_substrates':len(rows),'n_families':len(g),'family_size_distribution':{str(n):sum(len(v)==n for v in g.values()) for n in sorted({len(v) for v in g.values()})},'pooled_structure_mae':statistics.mean(r['structure_abs_error'] for r in rows),'pooled_pose_mae':statistics.mean(r['pose_abs_error'] for r in rows),'family_balanced_structure_mae':balanced_a,'family_balanced_pose_mae':balanced_b,'families_favouring_pose':sum(r['difference_structure_minus_pose']>1e-10 for r in families),'families_favouring_structure':sum(r['difference_structure_minus_pose']< -1e-10 for r in families),'substrates_favouring_pose':sum(r['difference_structure_minus_pose']>1e-10 for r in rows),'substrates_favouring_structure':sum(r['difference_structure_minus_pose']< -1e-10 for r in rows),'largest_family':largest,'excluding_largest_structure_mae':statistics.mean(r['structure_abs_error'] for r in other),'excluding_largest_pose_mae':statistics.mean(r['pose_abs_error'] for r in other),'input_sha256':{v:hashlib.sha256((IN/v).read_bytes()).hexdigest() for v in files.values()},'analysis_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limitations':'Post hoc descriptive summaries of archived fixed-cohort predictions; families have unequal sizes and models share training data. Excluding the largest family is not independent validation.'}
write(OUT/'paired_predictions.csv',rows);write(OUT/'family_results.csv',families);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
