import json,csv,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'revision/reviewer1_comment1'))
import initial_pair_replay as rr
sp=rr.sp
records=sp.read_jsonl(ROOT/rr.CONFIG['cmcpor']['records']); locked=set(rr.CONFIG['cmcpor']['audit'])
expected={'2aa':45,'2ab':39,'2ac':50,'2b':88,'2c':79,'2d':86,'2e':82,'2f':84,'2g':86,'2h':90,'2i':73,'2j':79,'2k':90,'2l':78,'2m':87,'2n':60,'2o':56,'2p':71,'2q':51,'2r':80,'2s':72,'2t':74,'2u':84,'2v':84,'2w':81,'2x':79,'6a':81,'6b':93,'6c':89,'6d':93,'6e':82,'6f':89,'6g':88,'6h':84,'6i':88,'6j':87,'6k':93,'6l':58,'6m':30,'6n':79,'6o':90,'6p':84,'6q':24}
actual={r['substrate_id']:r['outcome']['ee_percent'] for r in records if r['substrate_id'] not in locked};assert actual==expected,(set(actual)^set(expected),[(k,actual[k],expected[k]) for k in actual.keys()&expected.keys() if actual[k]!=expected[k]])
rows=sp.load_scope_rows(ROOT/rr.CONFIG['cmcpor']['records'],'cmcpor-fecl');table=sp.build_feature_table(rows,ROOT/rr.CONFIG['cmcpor']['features']); import numpy as np
assert len(rows)==50 and len(set(table.ids))==50 and len(table.stage2p_names)==248 and np.isfinite(table.matrix('rdkit_morgan_stage2p')).all()
features=sp.load_stage2p_features(ROOT/rr.CONFIG['cmcpor']['features']);assert all(x in features for x in expected) and all(table.stage2p_matrix[table.ids.index(x)].any() for x in expected)
for r in records:
 if r['substrate_id'].startswith('6'):
  r['condition']['condition_set_id']='wang2023-table4-cmcpor-sulfonyl';r['condition']['temperature_c']=40;r['condition']['source_note']='Table 4: 40 C; 6a also reports a separate 25 C result that is not used here.'
  if r['substrate_id']=='6q':r['outcome']['yield_qualifier']='less_than';r['outcome']['isolated_yield_percent']=5;r['outcome']['yield_source_note']='Table 4 reports <5%, not exact 5%.'
out=HERE/'results'/'cmcpor_source_corrected_copy.jsonl';out.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records))
for s in ['data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl','data/expansion/catalyst_rerun/cmcpor_uff_full/stage2p/features/stage2p-features.jsonl','expand/10.1002:anie.202218577/maintext.pdf']:
 print(s,hashlib.sha256((ROOT/s).read_bytes()).hexdigest())
print('PASS 26 aryl and 17 sulfonyl ee values match source Tables 1 and 4 for CMC-Por; 7 locked aryl excluded. All 43 feature rows available, finite and nonzero. Source-specific condition metadata corrected in revision-local ledger; 6q yield marked <5%.')
