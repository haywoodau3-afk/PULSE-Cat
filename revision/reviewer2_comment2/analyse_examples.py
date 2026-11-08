#!/usr/bin/env python3
import os,sys,csv,json,math,hashlib,statistics,warnings
from pathlib import Path
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT));import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from rdkit import Chem
from scripts import stage2_pose_interaction as inter

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
ids=['1a','1ah'];records={r['substrate_id']:r for r in (json.loads(l) for l in open(ROOT/'data/jacs_2025/stage2/curated-reaction-records.jsonl'))};
for sid in ids:assert records[sid]['condition']['temperature_c']==60 and records[sid]['catalyst_id']=='fe-p7-cl'
keynames=['pose_interaction.substrate_centroid_to_fe_distance_angstrom.mean','pose_interaction.nitrene_n_to_reported_c_distance_angstrom.mean'];metrics={};filepaths=[]
matfile=ROOT/'data/jacs_2025/stage2/features/full-scope-structure-pose-ee-matrix.csv';rows=readcsv(matfile);features=list(rows[0])[13:];X=np.array([[float(r[k]) for k in features] for r in rows]);y=np.array([float(r['target_value']) for r in rows]);act=X.std(axis=0)>0;feature_active=np.array(features)[act];X=X[:,act];ix={r['substrate_id']:i for i,r in enumerate(rows)};assert len(rows)==38 and len(features)==1241 and len(feature_active)==756
for sid in ids:
 rr=records[sid];nit=inter.stage1_pose_molecule(rr['structure']['nitrene_smiles']);mapping=inter.map_ids_to_stage1_atom_indices(rr,nit);site=mapping[rr['reaction_center']['reported_reactive_site']['atom_map_id']];nitidx=inter.ordered_substrate_indices(nit)[0];assert len(Chem.GetShortestPath(nit,nitidx,site))==5
 stage=ROOT/f'data/jacs_2025/stage1/panel/stage-1-smoke-{sid}.json';d=json.loads(stage.read_text());poses=d['pose_records'];best=min(poses,key=lambda r:(r['uff_pose_score'],r['score_rank']));assert best['score_rank']==1 and best['clash_screen_status']=='passed_covalent_radius_floor' and best['connectivity_preserved'] and best['frozen_core_preserved'];xyz=ROOT/best['fe_bound_assembly_xyz_path'];sdf=ROOT/best['uff_optimized_sdf_path'];assert xyz.exists() and sdf.exists();filepaths.extend([stage,xyz,sdf]);x=[r for r in readcsv(matfile) if r['substrate_id']==sid][0]
 interactions=[json.loads(l) for l in open(ROOT/'data/jacs_2025/stage2/features/pose-interaction.jsonl') if json.loads(l).get('substrate_id')==sid];assert len(interactions)==200
 for k in keynames:
  base=k.split('pose_interaction.',1)[1].rsplit('.mean',1)[0];observed=statistics.mean(r['feature_blocks']['pose_interaction'][base] for r in interactions);assert abs(observed-float(x[k]))<1e-8
 metrics[sid]={'ee_percent':rr['outcome']['ee_percent'],'substrate_smiles':rr['structure']['azide_smiles'],'nitrene_smiles':rr['structure']['nitrene_smiles'],'product_id':rr['product_id'],'temperature_c':rr['condition']['temperature_c'],'reactive_c_atom_map':rr['reaction_center']['reported_reactive_site']['atom_map_id'],'pose_id':best['pose_id'],'pose_score_rank':best['score_rank'],'pose_uff_score':best['uff_pose_score'],'n_retained_poses':len(poses),'assembly_xyz':str(xyz.relative_to(ROOT)),'substrate_sdf':str(sdf.relative_to(ROOT)),'pose_nitrene_index_zero_based':nitidx,'pose_reactive_c_index_zero_based':site,'frozen_core_atom_count':best['frozen_core_atom_count'],'features':{k:float(x[k]) for k in keynames},'prediction':{}}
 for mode, prefix in [('target','full-scope-'),('family','family-heldout-')]:
  for feat in ['structure','structure-pose']:
   fn=(prefix+feat+'-model-predictions.csv') if mode=='target' else (prefix+feat+'-ee-model-predictions.csv');p=ROOT/'data/jacs_2025/stage2/reports'/fn;z=next(r for r in readcsv(p) if r['target_substrate_id']==sid and r['model_name']=='elastic_net' and r['target_name']=='ee');metrics[sid]['prediction'][mode+'_'+feat]={'prediction':float(z['prediction']),'observed':float(z['observed_target_value']),'params':json.loads(z['selected_estimator_params'])};filepaths.append(p)
  # Refit structure-plus-pose held-out model using its exact archived train IDs and selected parameters.
  p=ROOT/'data/jacs_2025/stage2/reports'/((prefix+'structure-pose-model-predictions.csv') if mode=='target' else (prefix+'structure-pose-ee-model-predictions.csv'));z=next(r for r in readcsv(p) if r['target_substrate_id']==sid and r['model_name']=='elastic_net' and r['target_name']=='ee');train=[ix[a] for a in z['train_substrate_ids'].split('|')];assert sid not in z['train_substrate_ids'].split('|') and sid not in z['validation_substrate_ids'].split('|');params=json.loads(z['selected_estimator_params']);model=make_pipeline(StandardScaler(),ElasticNet(alpha=params['alpha'],l1_ratio=params['l1_ratio'],max_iter=20000,random_state=0));
  with warnings.catch_warnings():warnings.simplefilter('ignore');model.fit(X[train],y[train])
  pred=float(model.predict(X[[ix[sid]]])[0]);assert abs(pred-float(z['prediction']))<1e-6,(sid,mode,pred,z['prediction']);coef=model[-1].coef_;info={}
  for k in keynames:
   j=list(feature_active).index(k);info[k]={'standardised_coefficient':float(coef[j]),'training_std':float(model[0].scale_[j]),'target_standardised_value':float(model[0].transform(X[[ix[sid]]])[0,j])}
  metrics[sid]['prediction'][mode+'_pose_refit']={'prediction':pred,'n_training':len(train),'coefficients':info,'n_nonzero':int(np.count_nonzero(coef))}
print(json.dumps(metrics,indent=2));(P/'results'/'example_audit.json').write_text(json.dumps({'examples':metrics,'inputs_sha256':{str(x.relative_to(ROOT)):sha(x) for x in set(filepaths+[matfile,ROOT/'data/jacs_2025/stage2/features/pose-interaction.jsonl',ROOT/'data/jacs_2025/stage2/curated-reaction-records.jsonl'])},'screening_caveat':'Source matrix uses global label-blind zero-variance filtering before split; scaling and fitting use training rows only.'},indent=2)+'\n')
