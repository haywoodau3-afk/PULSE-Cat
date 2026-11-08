import os,sys,time
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import stage2_pose_interaction as s
source=ROOT/'revision/reviewer1_comment5/results/cmcpor_source_corrected_copy.jsonl'
reports=ROOT/'data/expansion/catalyst_rerun/cmcpor_uff_full/stage1/reports'
out=Path(__file__).resolve().parent/'corrected_cmc_pose_interaction.jsonl'
t=time.time(); rows=s.generate_pose_interactions(source,reports);s.write_jsonl(out,rows);print('rows',len(rows),'seconds',round(time.time()-t,1))
