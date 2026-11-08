import os,sys
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'));import initial_pair_replay as rr
import secondary_fixed_audit as a
rr.CONFIG['cmcpor']['features']=str((P/'results/corrected_cmcpor_stage2p.jsonl').relative_to(ROOT));rr.DEST=P/'results'/'corrected_shared_starts';a.main()
