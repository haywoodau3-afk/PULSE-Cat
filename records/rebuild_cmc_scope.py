import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'full_scope_cmc'
sys.path.insert(0,str(ROOT))
from scripts import stage2_full_scope_benchmark as s
records=ROOT/'revision/reviewer1_comment5/results/cmcpor_source_corrected_copy.jsonl'; pose=Path(__file__).resolve().parent/'corrected_cmc_pose_interaction.jsonl'; summary=ROOT/'data/expansion/catalyst_rerun/cmcpor_uff_full/stage2/features/pose-summary.jsonl'
for target,mode in [('ee','target_holdout'),('yield','target_holdout'),('ee','family_holdout'),('yield','family_holdout')]:
 name=f'{mode}_{target}'; matrix=OUT/f'{name}_matrix.csv'; report=OUT/f'{name}_report.json'; pred=OUT/f'{name}_predictions.csv'; splits=OUT/f'{name}_splits.json'; pm=OUT/f'{name}_pose_matrix.csv';pr=OUT/f'{name}_pose_report.json';pp=OUT/f'{name}_pose_predictions.csv';cr=OUT/f'{name}_comparison.json';ct=OUT/f'{name}_comparison.csv'
 result=s.run_comparison(records,matrix,report,pred,splits,pm,pr,pp,cr,ct,summary,pose,target,mode);print(name,s.best_summary_line(name,result),flush=True)
