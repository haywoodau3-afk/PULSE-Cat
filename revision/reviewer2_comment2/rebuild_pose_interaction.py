import os,sys,json,time
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R));from scripts import stage2_pose_interaction as s
start=time.time();rows=s.generate_pose_interactions(R/'revision/reviewer2_comment1/results/p7_source_corrected_copy.jsonl',R/'data/jacs_2025/stage1/panel');dest=P/'results/corrected_p7_pose_interaction.jsonl';s.write_jsonl(dest,rows);print('rows',len(rows),'seconds',round(time.time()-start,2))
