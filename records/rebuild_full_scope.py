import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'full_scope'
sys.path.insert(0,str(ROOT))
from scripts import stage2_full_scope_benchmark as s
records=ROOT/'revision/reviewer2_comment1/results/p7_source_corrected_copy.jsonl'
pose=ROOT/'revision/reviewer2_comment2/results/corrected_p7_pose_interaction.jsonl'
summary=ROOT/'data/jacs_2025/stage2/features/pose-summary.jsonl'
# Build every target-held-out and family-held-out ee/yield structure and structure+pose report under this folder.
for target,splitmode in [('ee','target_holdout'),('yield','target_holdout'),('ee','family_holdout'),('yield','family_holdout')]:
 name=f'{splitmode}_{target}'; matrix=OUT/f'{name}_matrix.csv'; report=OUT/f'{name}_report.json'; pred=OUT/f'{name}_predictions.csv'; splits=OUT/f'{name}_splits.json'; pose_matrix=OUT/f'{name}_pose_matrix.csv'; pose_report=OUT/f'{name}_pose_report.json'; pose_pred=OUT/f'{name}_pose_predictions.csv'; cmp_report=OUT/f'{name}_comparison.json';cmp_table=OUT/f'{name}_comparison.csv'
 result=s.run_comparison(records,matrix,report,pred,splits,pose_matrix,pose_report,pose_pred,cmp_report,cmp_table,summary,pose,target,splitmode)
 print(name,s.best_summary_line(name,result),flush=True)
