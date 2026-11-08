#!/usr/bin/env python3
"""Create a standalone figure of the prespecified paired comparisons."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parent/'results'
fig,axes=plt.subplots(1,2,figsize=(9.2,4.0),sharex=True,sharey=True,layout='constrained')
for ax,(domain,title) in zip(axes,[('p7','Fe(P7)Cl'),('cmcpor','Fe(CMC-Por)Cl')]):
 with (root/domain/'pair_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
 rng=np.random.default_rng(31)
 for y,key,color in [(1,'reported_minus_ud','#315c88'),(0,'random_minus_ud','#ba6b2b')]:
  x=np.asarray([float(row[key]) for row in rows]); jitter=rng.uniform(-.13,.13,len(x))
  ax.scatter(x,y+jitter,s=15,alpha=.60,c=color,linewidths=0,zorder=2)
  q1,med,q3=np.quantile(x,[.25,.5,.75]);ax.plot([q1,q3],[y,y],color='#111111',linewidth=3.2,zorder=3)
  ax.scatter([med],[y],marker='D',s=25,c='white',edgecolors='#111111',linewidths=.8,zorder=4)
 ax.axvline(0,color='#777777',linestyle='--',linewidth=.9,zorder=1)
 ax.set_title(title,fontsize=12,fontweight='bold');ax.set_yticks([1,0],['Source-order continuation','Random continuation']);ax.set_ylim(-.42,1.42)
 ax.grid(axis='x',color='#e4e4e4',linewidth=.7);ax.spines[['top','right']].set_visible(False)
 ax.tick_params(axis='both',labelsize=9)
fig.supxlabel('Comparator − uncertainty–diversity mean-prefix MAE (ee percentage points)\nPositive values favour uncertainty–diversity',fontsize=10)
fig.suptitle('Sensitivity to 50 shared starting pairs per catalyst',fontsize=13,fontweight='bold')
fig.savefig(root/'shared_start_sensitivity.png',dpi=300,facecolor='white',bbox_inches='tight');plt.close(fig)

project=Path(__file__).resolve().parents[2]
fig,axes=plt.subplots(1,2,figsize=(9.2,4.1),sharey=True,layout='constrained')
for ax,(domain,title,archive) in zip(axes,[('p7','Fe(P7)Cl','data/jacs_2025/scope_progression/learning-curve.csv'),('cmcpor','Fe(CMC-Por)Cl','data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/learning-curve.csv')]):
 with (root/domain/'learning_curves.csv').open(newline='') as f: curves=list(csv.DictReader(f))
 with (project/archive).open(newline='') as f: archived=list(csv.DictReader(f))
 for route,label,color in [('historical_order','Source-order continuation','#315c88'),('uncertainty_diversity','Uncertainty–diversity','#ba6b2b')]:
  data=[r for r in curves if r['route']==route];budgets=sorted({int(r['n_labeled']) for r in data})
  values=np.array([[float(r['mae']) for r in data if int(r['n_labeled'])==n] for n in budgets]);assert values.shape[1]==50
  med=np.median(values,axis=1);low,high=np.quantile(values,[.25,.75],axis=1)
  ax.plot(budgets,med,color=color,label=label+' median');ax.fill_between(budgets,low,high,color=color,alpha=.16)
  a=[r for r in archived if r['route']==route and r['replicate']=='0' and r['target']=='ee_percent' and r['model']=='ridge' and r['evaluation_pool']=='remaining_active' and r['mae']]
  a.sort(key=lambda r:int(r['n_labeled']));ax.plot([int(r['n_labeled']) for r in a],[float(r['mae']) for r in a],color=color,linestyle='--',linewidth=1.4,label=label+' archived')
 ax.set_title(title,fontweight='bold');ax.set_xlabel('Number of labelled substrates');ax.grid(color='#e5e5e5',linewidth=.6);ax.spines[['top','right']].set_visible(False)
axes[0].set_ylabel('Remaining-pool MAE (ee percentage points)')
axes[0].legend(fontsize=7,loc='upper right',frameon=False)
fig.suptitle('Shared-start learning curves and original archived trajectories',fontsize=12,fontweight='bold')
fig.savefig(root/'shared_start_learning_curves.png',dpi=300,facecolor='white',bbox_inches='tight');plt.close(fig)
