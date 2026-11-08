#!/usr/bin/env python3
"""Plot paired differences for the prespecified common-test analysis."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parent/'results/common_test'
fig,axes=plt.subplots(1,2,figsize=(9.2,4.0),sharex=True,sharey=True,layout='constrained')
for ax,(domain,title) in zip(axes,[('p7','Fe(P7)Cl'),('cmcpor','Fe(CMC-Por)Cl')]):
 with (root/domain/'split_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
 rng=np.random.default_rng(71)
 for y,key,color in [(1,'source_minus_ud','#315c88'),(0,'random_minus_ud','#ba6b2b')]:
  x=np.array([float(r[key]) for r in rows]);ax.scatter(x,y+rng.uniform(-.11,.11,len(x)),s=22,alpha=.7,c=color,linewidths=0,zorder=2)
  q1,med,q3=np.quantile(x,[.25,.5,.75]);ax.plot([q1,q3],[y,y],c='#111',linewidth=3,zorder=3);ax.scatter([med],[y],marker='D',s=30,c='white',edgecolors='#111',linewidths=.8,zorder=4)
 ax.axvline(0,color='#777',linestyle='--',linewidth=.9);ax.set_title(title,fontweight='bold',fontsize=12);ax.set_yticks([1,0],['Source-order continuation','Random continuation']);ax.set_ylim(-.4,1.4);ax.grid(axis='x',color='#e5e5e5',linewidth=.7);ax.spines[['top','right']].set_visible(False);ax.tick_params(labelsize=9)
fig.suptitle('Common held-out test sets: 20 overlapping splits per catalyst',fontsize=12,fontweight='bold')
fig.supxlabel('Comparator − uncertainty–diversity mean held-out MAE (ee percentage points)\nPositive values favour uncertainty–diversity',fontsize=10)
fig.savefig(root/'common_test_split_differences.png',dpi=300,facecolor='white',bbox_inches='tight');plt.close(fig)
