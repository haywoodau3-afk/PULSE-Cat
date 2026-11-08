from pathlib import Path
from docx import Document
from docx.shared import RGBColor
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
P=Path(__file__).resolve().parent;d=Document(P/'Supporting_Information_provisional.docx')
# Set the front notice to distinguish corrected sections from historical outputs still under audit.
p=d.paragraphs[0];p.clear();r=p.add_run('WORKING REVISION — NOT FOR SUBMISSION. Several archived pose-dependent tables and figures in the original SI were calculated with a faulty nitrene atom-index assumption. Corrected independent progression tables and the full 13-pair cross-catalyst scan are now included. Other historical pose-dependent analyses remain under audit and must not be relied upon unless explicitly regenerated and identified below.');r.bold=True;r.font.color.rgb=RGBColor(0xB0,0,0);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
anchor=next(x for x in d.paragraphs if x.text.startswith('S1 Study scope'))
def before(text,style=None):
 el=OxmlElement('w:p');anchor._p.addprevious(el);q=Paragraph(el,anchor._parent);q.add_run(text)
 if style:q.style=style
 return q
q=before('Correction update to the atom mapping and principal results','Heading 1')
q=before('The original pose-feature code sometimes assumed that molecular atom index zero was the nitrene nitrogen. For certain suffix-style nitrene SMILES, atom zero is carbon. The corrected generator maps the actual nitrene atom and uses that mapping when constructing nitrene-anchored geometry and selecting the transferable hydrogen. Source reaction outcomes and saved coordinates are unchanged; affected geometric features and dependent predictions were regenerated. Original values remain in the archived tables below for traceability, but they are superseded by this correction update when the same analysis is reported here.')
q=before('Across the checked 38-record Fe(P7)Cl development cohort, 12 Stage 2p records changed; across the regenerated 50-record Fe(CMC-Por)Cl set, 30 changed. The 1ah mean nitrene-N-to-reactive-carbon distance recalculated from 200 saved coordinates is 3.5815 Å, whereas the archived feature was 2.5386 Å. The audit files in the revision project give record-level counts and feature hashes. These changes affect prediction and acquisition analyses using pose-derived features.')
q=before('Table C1. Corrected core representation results for the Fe(P7)Cl 38-substrate Elastic Net comparison. MAE is in ee percentage points.')
t=d.add_table(rows=1,cols=4);t.style='Table Grid'
for c,v in zip(t.rows[0].cells,['Validation','Structure-only MAE','Structure + pose MAE','Relative reduction']):c.text=v
for row in [['Target held out','12.612','7.979','36.7%'],['Family held out','10.406','8.538','17.9%']]:
 cells=t.add_row().cells
 for c,v in zip(cells,row):c.text=v
q._p.addprevious(t._tbl)
q=before('The corrected family-level post hoc summary favours pose features for 11/17 families and 23/38 substrates; equal-weight family MAE is 11.99 for structure-only and 8.72 for structure plus pose. The largest family favours structure-only (5.25 versus 6.23). Four low-ee cases have mean signed prediction error +17.85 in target holdout and +18.56 in family holdout. These are descriptive analyses on one fixed dataset.')
q=before('Table C2. Corrected dedicated mean-prefix ee MAE reruns and corrected common-test acquisition comparisons. Dedicated replay and common-test metrics have different definitions and must not be combined.')
t2=d.add_table(rows=1,cols=5);t2.style='Table Grid'
for c,v in zip(t2.rows[0].cells,['Catalyst / analysis','Comparator','Reference MAE','Uncertainty–diversity MAE','Paired interpretation']):c.text=v
rows=[
['Fe(P7)Cl, dedicated route replay','Source order','25.508','7.475','70.7% lower mean-prefix MAE'],
['Fe(CMC-Por)Cl aryl, dedicated route replay','Source order','16.977','9.641','43.2% lower mean-prefix MAE'],
['Fe(P7)Cl, common test (20 splits)','Source order','20.710','13.718','19/20 splits favour UD; delta 6.992'],
['Fe(P7)Cl, common test (20 splits)','Random','15.167','13.718','15/20 splits favour UD; delta 1.449'],
['Fe(CMC-Por)Cl aryl, common test (20 splits)','Source order','16.330','13.834','11/20 splits favour UD; delta 2.496'],
['Fe(CMC-Por)Cl aryl, common test (20 splits)','Random','15.051','13.834','12/20 splits favour UD; delta 1.217']]
for row in rows:
 cells=t2.add_row().cells
 for c,v in zip(cells,row):c.text=v
q._p.addprevious(t2._tbl)
q=before('Additional corrected acquisition findings: across 50 shared starts, source-order-minus-UD mean differences were 9.831 ee points for Fe(P7)Cl and 4.842 for Fe(CMC-Por)Cl aryl records; 50/50 and 45/50 starts favoured UD. The seven-record locked CMC audit mean was +3.879 (conditional bootstrap interval 2.694–5.054), favouring UD in 43/50 sampled starts. The 21-setting weight-grid default ranked 8/21 for P7 and 11/21 for CMC. The corrected factorial mean MAEs (structure/source, structure/UD, pose/source, pose/UD) were 11.34, 12.07, 20.71, 13.72 for P7 and 9.62, 10.77, 16.33, 13.83 for CMC. All intervals and ranks are conditional on overlapping retrospective splits and fixed observed datasets.')
q=before('Corrected baseline, endpoint, and substrate-class findings: in the 20-split common-test ee analysis, QBC / expected-improvement / Thompson mean MAE was 13.078 / 13.896 / 14.418 for P7 and 13.400 / 16.408 / 15.331 for the CMC aryl cohort, compared with UD 13.718 and 13.834. Corrected common-test yield MAE for source order / UD / random was 21.11 / 18.28 / 20.85 for P7 and 25.48 / 23.49 / 24.53 for CMC; mean comparisons favour UD for both CMC comparators, with split-level variation. Corrected sulfonyl-only source / UD / random MAE was 17.98 / 19.22 / 19.63. These outcomes do not identify chemical mechanisms.')
q=before('The corrected P7 Stage 2pp Elastic Net target-held-out MAE changed from 8.270 for Stage 2p to 10.464 after adding occupancy/flexibility fields. The Stage 1-v2 selection and dependent Stage 2-v2/Stage 3a seed-pilot models have now been regenerated: 148/600 selected pose identities changed across four of 12 substrate sets, and the corrected 11-record ee model cohort gives MAEs of 6.775 (Stage 2 seed baseline), 15.201 (Stage 2-v2 selected poses), 6.886 (graph-only Stage 3a-alt), and 13.201 (Stage 3a reference/shell). The earlier 12-record shell comparison of 21.208 versus 22.019 is superseded.')
q=before('The corrected independent progression tables S9–S12 and updated progression figures S5–S6 replace the archived values below. Across all three estimators, uncertainty–diversity has lower AUC-MAE than reported order for Fe(P7)Cl and the Fe(CMC-Por)Cl aryl cohort on both ee and yield; diversity-first remains lower than uncertainty–diversity for CMC ee with Tanimoto-kNN. A corrected scan of all 13 shared aryl identities confirms that P7 1i / CMC 2r remains the largest-Jensen–Shannon-divergence pair (0.0310 bits; total variation 0.1719; Bhattacharyya overlap 0.9781). Corrected CREST/GFN2-xTB ablation estimates are shown in Tables S6–S7; their substrate-bootstrap intervals include zero. Other historical pose-dependent outputs not listed in the correction update remain under audit.')
d.save(P/'Supporting_Information_corrected_working.docx')
print(P/'Supporting_Information_corrected_working.docx')
