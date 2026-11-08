import os,sys
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'revision/reviewer1_comment2'));import weight_sensitivity as w
for d in ['p7','cmcpor']:w.rr.CONFIG[d]['features']=str((P/'results'/f'corrected_{d}_stage2p.jsonl').relative_to(ROOT))
w.DEST=P/'results'/'corrected_weight_sensitivity';w.main(sys.argv[1])
