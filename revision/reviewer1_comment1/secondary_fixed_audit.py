#!/usr/bin/env python3
"""Prespecified secondary check on the seven locked CMC ee records."""
import json, random, statistics
from pathlib import Path
import numpy as np
import initial_pair_replay as rr
sp=rr.sp

def main():
 table,pool=rr.load('cmcpor');cfg=rr.CONFIG['cmcpor'];out=rr.DEST/'cmcpor'
 pairs=rr.rows_csv(out/'initial_pairs.csv');assert len(pairs)==50
 audit=[table.ids.index(x) for x in cfg['audit']]
 assert len(audit)==7 and not set(audit)&set(pool)
 assert all(sp.outcome_value(table.rows[i].record,'ee_percent') is not None for i in audit)
 budgets={6,13,20};rows=[];results=[];predictions=[]
 for p in pairs:
  pair=[table.ids.index(p['substrate_1']),table.ids.index(p['substrate_2'])];pair_id=int(p['pair_id']);score={}
  for route in ['historical_order','uncertainty_diversity']:
   old=sp.seed_indices;sp.seed_indices=lambda t,pool_,r,rng:list(pair)
   try:
    _,audit_rows,pred_rows,_=sp.simulate_route(table,'ee_percent',rr.FEATURE,pool,audit,route,0,random.Random(rr.SEED),budgets)
   finally:sp.seed_indices=old
   q=[r for r in audit_rows if r['model']=='ridge' and r['n_labeled'] in budgets]
   assert {r['n_labeled'] for r in q}==budgets and all(r['n_evaluated']==7 for r in q)
   for r in q:rows.append({'pair_id':pair_id,'substrate_1':p['substrate_1'],'substrate_2':p['substrate_2'],'route':route,'n_labeled':r['n_labeled'],'n_evaluated':r['n_evaluated'],'mae':r['mae']})
   for r in pred_rows:
    if r['model']=='ridge' and r['n_labeled'] in budgets:
     predictions.append({'pair_id':pair_id,'route':route,'n_labeled':r['n_labeled'],'substrate_id':r['substrate_id'],'observed_value':r['observed_value'],'predicted_value':r['predicted_value']})
   score[route]=statistics.mean(r['mae'] for r in q)
  results.append({'pair_id':pair_id,'substrate_1':p['substrate_1'],'substrate_2':p['substrate_2'],'reported_order_mean_mae':score['historical_order'],'ud_mean_mae':score['uncertainty_diversity'],'reported_minus_ud':score['historical_order']-score['uncertainty_diversity']})
  print('CMC fixed audit pair',pair_id,'/',len(pairs),flush=True)
 rr.output(out/'fixed_audit_curves.csv',rows);rr.output(out/'fixed_audit_pair_results.csv',results);rr.output(out/'fixed_audit_predictions.csv',predictions)
 x=np.array([r['reported_minus_ud'] for r in results]);rng=np.random.default_rng(rr.SEED+202);boot=rng.choice(x,size=(10000,len(x)),replace=True).mean(axis=1)
 summary={'audit_ids':cfg['audit'],'audit_size':len(audit),'budgets':sorted(budgets),'n_pairs':len(pairs),'metric':'mean Ridge MAE on the same locked seven-record set over three budgets','mean_reported_minus_ud':float(x.mean()),'median_reported_minus_ud':float(np.median(x)),'paired_difference_2.5_97.5_percentiles':[float(z) for z in np.quantile(x,[.025,.975])],'fraction_positive':float(np.mean(x>0)),'mean_bootstrap_ci_95':[float(z) for z in np.quantile(boot,[.025,.975])],'interpretation':'conditional on the observed seven-record audit set and sampled initial pairs; not a new-catalyst confidence interval','wrapper_sha256':rr.sha(Path(__file__))}
 (out/'fixed_audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
