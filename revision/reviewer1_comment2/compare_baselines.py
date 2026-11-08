import csv
from pathlib import Path
base=Path(__file__).parent
for domain in ('p7','cmcpor'):
    sens=base/'results'/'weight_sensitivity'/domain
    prev=base.parent/'reviewer1_comment1'/'results'/'common_test'/domain/'split_results.csv'
    with prev.open() as f: baseline={int(r['split_id']):r for r in csv.DictReader(f)}
    with (sens/'split_results.csv').open() as f: rows=list(csv.DictReader(f))
    out=[]
    for wid in sorted({int(r['weight_id']) for r in rows}):
        group=[r for r in rows if int(r['weight_id'])==wid]
        assert len(group)==20 and {int(r['split_id']) for r in group}==set(baseline)
        item={k:group[0][k] for k in ('weight_id','w_diversity','w_uncertainty','w_family_coverage')}
        for label,col in [('source','source_mae'),('random','random_mae')]:
            diffs=[float(baseline[int(r['split_id'])][col])-float(r['mean_heldout_mae']) for r in group]
            item[label+'_mean_difference']=sum(diffs)/len(diffs)
            item[label+'_splits_favouring_weight']=sum(x>1e-10 for x in diffs)
        out.append(item)
    with (sens/'baseline_comparisons.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
    print(domain)
    for label in ('source','random'):
        vals=[r[label+'_mean_difference'] for r in out]
        print(label,'positive means',sum(x>0 for x in vals),'range',min(vals),max(vals),'split wins range',min(r[label+'_splits_favouring_weight'] for r in out),max(r[label+'_splits_favouring_weight'] for r in out))
    default=next(r for r in out if (r['w_diversity'],r['w_uncertainty'],r['w_family_coverage'])==('0.4','0.4','0.2'))
    print('default',default)
    for r in rows:
        if int(r['weight_id'])==int(default['weight_id']): assert abs(float(r['mean_heldout_mae'])-float(baseline[int(r['split_id'])]['ud_mae']))<1e-9
