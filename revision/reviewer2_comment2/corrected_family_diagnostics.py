import csv,json,statistics
from pathlib import Path
from collections import defaultdict
P=Path(__file__).resolve().parent;R=P.parents[1]
def read(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
pose={r['substrate_id']:r for r in read(P/'results/corrected_pose_elasticnet_predictions.csv') if r['mode']=='family'}
old={r['target_substrate_id']:r for r in read(R/'data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-predictions.csv') if r['target_name']=='ee' and r['model_name']=='elastic_net'}
assert set(pose)==set(old) and len(pose)==38
families=defaultdict(list)
for sid,z in old.items():
 p=pose[sid];assert float(p['observed_ee'])==float(z['observed_target_value']);families[z['family_id']].append((abs(float(z['prediction'])-float(z['observed_target_value'])),float(p['abs_error'])))
out={'n_families':len(families),'families_favour_corrected_pose':sum(statistics.mean(a for a,b in x)>statistics.mean(b for a,b in x) for x in families.values()),'substrates_favour_corrected_pose':sum(a>b for x in families.values() for a,b in x),'family_balanced_structure_mae':statistics.mean(statistics.mean(a for a,b in x) for x in families.values()),'family_balanced_corrected_pose_mae':statistics.mean(statistics.mean(b for a,b in x) for x in families.values()),'largest_family':max(families,key=lambda z:len(families[z])),'largest_family_structure_mae':statistics.mean(a for a,b in max(families.values(),key=len)),'largest_family_corrected_pose_mae':statistics.mean(b for a,b in max(families.values(),key=len))}
(P/'results/corrected_family_diagnostics.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
