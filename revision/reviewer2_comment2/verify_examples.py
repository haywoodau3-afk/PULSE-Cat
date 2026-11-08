import os,sys,json,hashlib,csv,statistics
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT));import numpy as np
from rdkit import Chem
from scripts import stage2_pose_interaction as si
from PIL import Image
m=json.load(open(P/'results/example_audit.json'));results=[]
for sid,v in m['examples'].items():
 report=json.load(open(ROOT/f'data/jacs_2025/stage1/panel/stage-1-smoke-{sid}.json'));poses=report['pose_records'];assert len(poses)==200
 mol=si.stage1_pose_molecule(v['nitrene_smiles']);imap=si.stage1_index_to_assembly_index(mol,214);N=imap[v['pose_nitrene_index_zero_based']];C=imap[v['pose_reactive_c_index_zero_based']];heavy=[imap[a.GetIdx()] for a in mol.GetAtoms() if a.GetAtomicNum()>1];nc=[];cf=[]
 for pose in poses:
  a=si.parse_xyz(ROOT/pose['fe_bound_assembly_xyz_path']);assert a[46]['element']=='Fe' and a[N]['element']=='N' and a[C]['element']=='C';nc.append(float(np.linalg.norm(a[N]['xyz']-a[C]['xyz'])));cf.append(float(np.linalg.norm(np.mean([a[i]['xyz'] for i in heavy],axis=0)-a[46]['xyz'])))
 target=v['features'];archived_nc=target['pose_interaction.nitrene_n_to_reported_c_distance_angstrom.mean'];assert abs(statistics.mean(cf)-target['pose_interaction.substrate_centroid_to_fe_distance_angstrom.mean'])<1e-5;assert (abs(statistics.mean(nc)-archived_nc)<1e-5) == (sid=='1a')
 chosen=ROOT/v['assembly_xyz'];export=P/'results'/f'{sid}_selected_assembly.xyz';assert hashlib.sha256(chosen.read_bytes()).digest()==hashlib.sha256(export.read_bytes()).digest();molfile=Chem.MolFromMolFile(str(P/'results'/f'{sid}_substrate.mol'));original=Chem.MolFromSmiles(v['substrate_smiles']);assert Chem.MolToSmiles(Chem.RemoveHs(molfile))==Chem.MolToSmiles(original)
 results.append({'substrate':sid,'n_geometries_directly_recomputed':200,'nitrene_N_to_reactive_C_mean_corrected':statistics.mean(nc),'nitrene_N_to_reactive_C_archived':archived_nc,'archived_N_distance_is_correct':abs(statistics.mean(nc)-archived_nc)<1e-5,'substrate_centroid_to_Fe_mean':statistics.mean(cf),'rank1_N_to_C':nc[0],'rank1_centroid_to_Fe':cf[0],'exported_assembly_matches_archive':True,'molfile_matches_source_smiles':True,'heldout_model_refits':'independently checked in analyse_examples.py'})
img=Image.open(P/'results/substrate_examples.png');assert img.size==(1860,1590)
(P/'validation_report.json').write_text(json.dumps({'status':'verified; archived nitrene feature incorrect for 1ah','examples':results,'figure_dimensions':img.size,'limitations':'Pose rank does not establish thermodynamic population; model refits reproduce archived pipeline including label-blind global variance filtering.'},indent=2)+'\n');print(json.dumps(results,indent=2))
