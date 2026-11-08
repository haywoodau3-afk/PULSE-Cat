import os,sys,time,json,tempfile
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');P=Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R));from scripts import stage2p_representation as s
sid='1ah';records=s.read_jsonl(R/'data/jacs_2025/stage2/curated-reaction-records.jsonl');record=next(r for r in records if r['substrate_id']==sid);report=json.load(open(R/f'data/jacs_2025/stage1/panel/stage-1-smoke-{sid}.json'));start=time.time()
with tempfile.TemporaryDirectory() as tmp:row=s.generate_substrate_feature_row(record,report,Path(tmp))
old=next(r for r in s.read_jsonl(R/'data/jacs_2025/stage2/features/stage2p-features.jsonl') if r['substrate_id']==sid)
a={k:v for b in row['feature_blocks'].values() for k,v in b.items()};b={k:v for z in old['feature_blocks'].values() for k,v in z.items()};diff={k:float(a[k])-float(b[k]) for k in a if abs(float(a[k])-float(b[k]))>1e-8};out={'substrate':sid,'total_fields':len(a),'changed_fields':len(diff),'max_abs_change':max(abs(v) for v in diff.values()),'elapsed_seconds':time.time()-start,'example_differences':dict(list(diff.items())[:8])};(P/'results/1ah_stage2p_corrected.json').write_text(json.dumps(row)+'\n');(P/'results/1ah_stage2p_impact.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
