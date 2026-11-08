from pathlib import Path
import csv
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
P=Path(__file__).parent;PRE=P.parent/'reviewer1_comment3'
def find(d,s):
 a=[p for p in d.paragraphs if s in p.text];assert len(a)==1,(s,len(a));return a[0]
def rep(d,old,new):
 a=[r for p in d.paragraphs for r in p.runs if old in r.text];assert len(a)==1,(old,len(a));a[0].text=a[0].text.replace(old,new);a[0].font.highlight_color=WD_COLOR_INDEX.YELLOW
def after(a,t):
 e=OxmlElement('w:p');a._p.addnext(e);p=Paragraph(e,a._parent);p.style=a.style;p.add_run(t).font.highlight_color=WD_COLOR_INDEX.YELLOW;return p
def before(a,t,style='Normal'):
 e=OxmlElement('w:p');a._p.addprevious(e);p=Paragraph(e,a._parent);p.style=style;p.add_run(t).font.highlight_color=WD_COLOR_INDEX.YELLOW;return p
m=Document(PRE/'Manuscript_comment3_revised.docx')
rep(m,'prediction relative to structure-only features, with the largest benefit under target-held-out validation and a smaller improvement when complete substrate families were withheld. ','prediction relative to structure-only features; the family-held-out improvement was 10.3% and varied across the small, imbalanced set of substrate families. ')
rep(m,'The smaller family-held-out improvement indicates that catalyst-referenced geometry supplies useful information within the studied chemical domain but is less powerful when extrapolating across complete substrate families. The two protocols therefore support different levels of inference: the target-held-out result quantifies interpolation among represented chemistry, whereas the family-held-out result provides the more demanding test of transfer across family boundaries.','The 10.3% family-held-out reduction corresponds to 1.07 ee points and is modest relative to the baseline error. It does not establish reliable predictions for any new substrate family. The 31.9% target-held-out reduction and 10.3% family-held-out reduction use different splits and fitted models; their numerical difference is descriptive and is not a statistical test of a general extrapolation penalty. Target holdout tests prediction with individual substrates withheld, while family holdout withholds a predefined substrate family within the same catalyst dataset.')
a=find(m,'The 10.3% family-held-out reduction corresponds')
after(a,'A post hoc breakdown of the 38 paired predictions shows lower pose MAE in 11 of 17 families and lower absolute error for 25 of 38 substrates. The largest family contains 12 substrates and favours structure-only (MAE 5.25 versus 6.44 ee points). Equal weighting of family MAEs gives 11.99 versus 9.84, but nine families have only one substrate and this sensitivity summary is not independent validation (SI Section S11). The modest pooled gain and family-to-family variation constrain claims about new substrate classes, which are relevant when extending a catalyst scope. Prediction for new catalysts or reaction classes remains untested by this family holdout.')
lim=find(m,'The principal limitations accordingly apply')
after(lim,'The family-held-out representation benchmark is limited to 17 unevenly sized, predefined substrate families from one iron-porphyrin dataset; nine families are singletons. Independent studies with broader chemical families, more examples per family and prospectively selected substrates are needed to assess extrapolation to new substrate families and catalysts.')
con=find(m,'Selected catalyst-referenced descriptors added predictive value')
after(con,'The selected pose representation yielded a 1.07 ee-point pooled family-held-out improvement in this cohort, with heterogeneous family-level results; its value for new families and catalysts requires independent validation.')
find(m,'Table 2. Central matched acquisition comparison').paragraph_format.page_break_before=True
m.save(P/'Manuscript_comment4_revised.docx')
s=Document(PRE/'Supporting_Information_comment3_revised.docx');anchor=find(s,'Declaration of AI-assisted manuscript preparation')
before(anchor,'S11 Family-held-out prediction diagnostics','Heading 1')
before(anchor,'The archived structure-only and structure-plus-pose Elastic Net ee predictions were paired by substrate and checked against the 17 family-held-out split definitions. All 38 target IDs, outcomes, and training and validation memberships matched between feature arms; no held-out family member was included in its training or validation set. Recalculating absolute errors reproduces the published pooled MAEs of 10.406 and 9.334 ee points. The same 38 substrates appear in the target-held-out benchmark, whose distinct splits and models give 12.612 and 8.583. The difference between the two percentage reductions is descriptive and is not a statistical comparison of the protocols.')
before(anchor,'There are nine singleton families, four families of two, three of three, and one of 12. Pose lowered family MAE in 11/17 families and absolute error in 25/38 substrates. Family-balanced MAEs, averaging the 17 family MAEs equally, were 11.99 and 9.84 ee points for structure-only and structure plus pose. The 12-member diaryl-ethyl-aryl-substituted family favoured structure-only (5.25 versus 6.44). Excluding it gives pooled MAEs 12.79 and 10.67 over 26 substrates. Both alternative summaries are post hoc descriptions of the same observations; they are not independent validation or a basis to discard the largest family.')
before(anchor,'Table S20. Family-held-out Elastic Net ee MAEs. Positive difference (structure-only minus structure plus pose) favours the pose representation. MAEs are in ee points; n is the number of held-out substrates in the family.')
with (P/'results/family_results.csv').open(newline='') as f:rows=list(csv.DictReader(f))
t=s.add_table(rows=1,cols=5);t.style='Table Grid';t.autofit=False
for i,w in enumerate([2.75,.4,.95,.95,1.05]):t.columns[i].width=Inches(w)
headers=['Substrate family','n','Structure','+ pose','Difference']
for c,v in zip(t.rows[0].cells,headers):c.text=v
trPr=t.rows[0]._tr.get_or_add_trPr(); el=OxmlElement('w:tblHeader');el.set(qn('w:val'),'true');trPr.append(el)
for r in rows:
 c=t.add_row().cells
 vals=[r['family_id'],r['n'],f"{float(r['structure_mae']):.2f}",f"{float(r['pose_mae']):.2f}",f"{float(r['difference_structure_minus_pose']):+.2f}"]
 for cell,val in zip(c,vals):cell.text=val
for row in t.rows:
 for cell in row.cells:
  for para in cell.paragraphs:
   para.paragraph_format.space_after=Pt(0)
   for run in para.runs:run.font.size=Pt(8);run.font.highlight_color=WD_COLOR_INDEX.YELLOW
anchor._p.addprevious(t._tbl)
before(anchor,'The family labels define groups within this one Fe(P7)Cl dataset. Small, unequal family sizes and overlapping training sets limit inference; the reported summaries do not establish population-level significance or prediction accuracy for independent new substrate families, new catalysts or reaction classes. Paired predictions, family IDs, source-file hashes and analysis code are retained in the accompanying analysis records.')
find(s,'Table S20. Family-held-out Elastic Net ee MAEs').paragraph_format.page_break_before=True
s.save(P/'Supporting_Information_comment4_revised.docx')
