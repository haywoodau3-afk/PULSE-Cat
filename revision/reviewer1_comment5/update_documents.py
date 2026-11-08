from pathlib import Path
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
P=Path(__file__).parent; PRE=P.parent/'reviewer1_comment4'
def find(d,text):
 a=[p for p in d.paragraphs if text in p.text]; assert len(a)==1,(text,len(a));return a[0]
def replace(d,old,new):
 rs=[r for p in d.paragraphs for r in p.runs if old in r.text];assert len(rs)==1,(old,len(rs));rs[0].text=rs[0].text.replace(old,new);rs[0].font.highlight_color=WD_COLOR_INDEX.YELLOW
def after(a,text,style=None):
 e=OxmlElement('w:p');a._p.addnext(e);p=Paragraph(e,a._parent);p.style=style or a.style;p.add_run(text).font.highlight_color=WD_COLOR_INDEX.YELLOW;return p
def before(a,text,style='Normal'):
 e=OxmlElement('w:p');a._p.addprevious(e);p=Paragraph(e,a._parent);p.style=style;p.add_run(text).font.highlight_color=WD_COLOR_INDEX.YELLOW;return p
m=Document(PRE/'Manuscript_comment4_revised.docx')
replace(m,'Fe(P7)Cl and Fe(CMC-Por)Cl, respectively.','Fe(P7)Cl and the aryl-only Fe(CMC-Por)Cl cohort, respectively.')
replace(m,'33 aryl substrates and 17 sulfonyl controls','33 aryl and 17 sulfonyl substrate records')
replace(m,'with substrate-class-specific protocol differences.','with substrate-class-specific protocol differences. The sulfonyl scope was reported at 40 °C in toluene under 410 nm irradiation, with no Boc2O listed in its scope conditions; an additional 25 °C result was reported for 6a, whose 81% ee at 40 °C is used here.')
a=find(m,'A matched factorial analysis crossed structure-only')
after(a,'To assess the aryl-only restriction, we also evaluated Fe(CMC-Por)Cl with a mixed aryl/sulfonyl candidate pool using 20 overlapping stratified common-test splits (three aryl and two sulfonyl held out), three shared aryl starting pairs and label budgets of 2, 6, 10, 15 and 20. The same held-out sets and starts were used for the aryl-only pool. A separate 20-split sulfonyl-only replay used three held-out sulfonyl substrates and budgets of 2, 6, 10 and 13. We retained the existing Ridge features and acquisition weights (SI Section S12).')
a=find(m,'In the matched factorial analysis, mean held-out MAE')
after(a,'In the expanded Fe(CMC-Por)Cl analysis, aryl-only versus mixed-pool uncertainty–diversity gave held-out aryl MAEs of 14.22 versus 14.36 and sulfonyl MAEs of 19.03 versus 16.97 ee points; the mixed pool improved sulfonyl error in 12/20 splits and aryl error in 8/20. In a separate sulfonyl-only replay, source order, uncertainty–diversity and random gave 17.51, 18.61 and 18.71 ee points, respectively. Mixed-pool source order selected no sulfonyl records through budget 20, whereas uncertainty–diversity selected 6.95 on average. These small retrospective comparisons change candidate pool and training composition together and do not establish a general acquisition advantage (SI Section S12).')
a=find(m,'The principal limitations accordingly apply')
after(a,'The Fe(CMC-Por)Cl aryl and sulfonyl scopes were reported under different conditions, and reaction temperature and additive are not encoded in the features. Substrate class and protocol are therefore confounded in the expanded analysis. The original 33.2% comparison remains specific to the aryl cohort and cannot be extended to the complete catalyst scope. The source ledger also requires correction of sulfonyl condition metadata and the less-than qualifier for the 6q yield (SI Section S12).')
for r in find(m,'The principal literature conditions also distinguish').runs:
 if r.text == '°': r.font.name='Times New Roman'
m.save(P/'Manuscript_comment5_revised.docx')
s=Document(PRE/'Supporting_Information_comment4_revised.docx')
replace(s,'33 aryl substrates and 17 sulfonyl controls','33 aryl and 17 sulfonyl substrate records')
for t in s.tables:
 for row in t.rows:
  for c in row.cells:
   for p in c.paragraphs:
    for r in p.runs:
     if 'sulfonyl substrates are a pathway control.' in r.text:
      r.text=r.text.replace('sulfonyl substrates are a pathway control.','the original acquisition analysis used the aryl cohort only.');r.font.highlight_color=WD_COLOR_INDEX.YELLOW
a=find(s,'Declaration of AI-assisted manuscript preparation')
before(a,'S12 Fe(CMC-Por)Cl substrate-class scope and sensitivity','Heading 1')
before(a,'The source paper reports aryl and arylsulfonyl azide scopes under different conditions: the aryl scope at −10 °C with Boc2O, and the sulfonyl scope at 40 °C in toluene under 410 nm light, with no Boc2O listed in the latter scope conditions. An additional 25 °C result is given for 6a; its 81% ee at 40 °C was used. The 50-record ledger contains 33 aryl and 17 sulfonyl records. Seven aryl audit records were excluded from all analyses described here. The original acquisition comparison uses 26 active aryl records and does not establish performance across both substrate classes.')
before(a,'We checked the 26 active aryl and 17 sulfonyl ee values against the source scope tables. The original curated ledger assigns −10 °C to the sulfonyl records, although the source sulfonyl scope is at 40 °C; it also records the 6q yield as 5%, whereas the source reports <5%. A revision-local corrected copy retains the yield upper-bound qualifier. The original distributed ledger must be corrected before release. These analyses use ee, not yield; temperature and Boc2O are not encoded in the features, so correcting these metadata does not change the present ee calculations. Class, reaction conditions and other scope differences are confounded.')
before(a,'For the expanded-pool replay, 20 deterministic overlapping splits held out three aryl and two sulfonyl records; three shared aryl starting pairs per split were used with budgets 2, 6, 10, 15 and 20. We compared source order, uncertainty–diversity and the average of three random continuations per start, using the existing Ridge features and frozen acquisition weights. Both aryl-only and mixed candidate pools were evaluated on the same held-out records. MAEs were averaged equally over budgets and starts within each split, then over splits. A separate sulfonyl-only replay held out three of 17 sulfonyl records in each of 20 overlapping splits, with three starts and budgets 2, 6, 10 and 13.')
before(a,'In the mixed-pool replay, mean MAEs for source order / uncertainty–diversity / random were 17.14 / 15.41 / 16.71 ee points overall, 14.80 / 14.36 / 16.19 for aryl tests and 20.64 / 16.97 / 17.49 for sulfonyl tests. The corresponding aryl-only uncertainty–diversity MAEs were 16.15 overall, 14.22 aryl and 19.03 sulfonyl. Mixed-pool uncertainty–diversity had lower sulfonyl and aryl errors in 12/20 and 8/20 splits, respectively, compared with aryl-only uncertainty–diversity. The source route selected no sulfonyl records through budget 20; uncertainty–diversity selected 6.95 on average at budget 20. Thus the source-order comparison is class-imbalanced.')
before(a,'In the separate sulfonyl-only replay, source-order / uncertainty–diversity / random MAEs were 17.51 / 18.61 / 18.71; uncertainty–diversity had lower error than source order in 6/20 splits and random in 10/20. This replay uses different test sets and budgets from the mixed analysis. Candidate pool, training composition and acquisition path differ jointly; the small overlapping splits are retrospective and cannot identify isolated causal effects, population significance or prospective performance. Split definitions, selections, predictions, input hashes, source audit and validation checks are retained in the accompanying analysis records.')
s.save(P/'Supporting_Information_comment5_revised.docx')
