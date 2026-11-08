from pathlib import Path
import csv, statistics
root=Path(__file__).resolve().parent
expected={"p7":6.992186972893537,"cmcpor":2.50}
for domain,target in expected.items():
 p=root/"records"/"corrected_project"/"analysis_runs"/"corrected_common_test"/domain/"split_results.csv"
 with p.open(newline="") as f: rows=list(csv.DictReader(f))
 assert len(rows)==20,(domain,len(rows))
 observed=statistics.mean(float(r["source_minus_ud"]) for r in rows)
 assert abs(observed-target)<(0.01 if domain=="cmcpor" else 1e-9),(domain,observed)
 print(f"{domain}: source minus uncertainty–diversity = {observed:.4f} ee points across {len(rows)} saved splits")
print("These checks aggregate saved results; they do not rerun model training.")
