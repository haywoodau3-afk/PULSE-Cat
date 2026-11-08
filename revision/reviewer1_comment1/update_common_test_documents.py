#!/usr/bin/env python3
"""Add the repeated common-test results to the existing comment 1 revisions."""
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from update_documents import replacement,insert_after,before,cell_text,keep_captions_with_content

HERE=Path(__file__).resolve().parent
def find(d,needle):
    found=[p for p in d.paragraphs if needle in p.text]
    assert len(found)==1,(needle,len(found))
    return found[0]

def main_doc():
    d=Document(HERE/'Manuscript_revised.docx')
    p=find(d,'a seven-substrate fixed audit for Fe(CMC-Por)Cl gave mixed results.')
    replacement(p,'a seven-substrate fixed audit for Fe(CMC-Por)Cl gave mixed results.','a seven-substrate fixed audit for Fe(CMC-Por)Cl gave mixed results. Additional repeated common-test splits in both datasets also showed variation across held-out sets.')
    p=find(d,'To examine starting-scope sensitivity, 50 distinct initial substrate pairs')
    insert_after(d,p,('To compare predictions on common test substrates in both systems, a further retrospective analysis sampled 20 outer splits per catalyst, holding out six Fe(P7)Cl or five Fe(CMC-Por)Cl ee-labelled records per split. Three initial pairs per split were shared by source-order continuation, uncertainty–diversity and random continuation; the random score averaged three continuations per pair. Ridge MAE on the same held-out records was averaged at 2, 6, 10, 15 and 20 active labels and then across the three initial pairs within each split. The previously locked seven-record Fe(CMC-Por)Cl audit remained excluded. Outer splits overlap and come from the same fixed datasets (SI Section S8).'))
    p=find(d,'The fixed-test-set check gives a more limited result.')
    insert_after(d,p,('In the repeated common-test analysis, the mean paired source-order-minus-uncertainty–diversity MAE difference across 20 splits was 2.85 ee points for Fe(P7)Cl and 1.43 for Fe(CMC-Por)Cl; 17/20 and 11/20 splits, respectively, favoured uncertainty–diversity. Against random continuation, the mean differences were 0.37 and 1.06 ee points, and 12/20 and 14/20 splits favoured uncertainty–diversity. The Fe(CMC-Por)Cl source-order mean is influenced by one +17.76-point split; its median paired difference was 0.54. These overlapping retrospective splits are not independent datasets and do not establish a uniform advantage or population-level significance (Table S18 and Fig. S10).'))
    p=find(d,'The principal limitations accordingly apply to both components')
    old='sensitivity to initial pairs has been examined only in the two observed datasets and has not been exhaustively characterised for broader starting panels'
    new='sensitivity to initial pairs and common test sets has been examined only within the two observed datasets using overlapping splits, and has not been exhaustively characterised for broader starting panels'
    replacement(p,old,new)
    p=find(d,'Selected catalyst-referenced descriptors added predictive value')
    old='the small fixed Fe(CMC-Por)Cl audit did not show a consistent advantage.'
    new='the small fixed Fe(CMC-Por)Cl audit and the repeated common-test splits did not show a uniform advantage.'
    replacement(p,old,new)
    keep_captions_with_content(d);d.save(HERE/'Manuscript_common_test_revised.docx')

def add_caption(doc,anchor,label,body):
    p=before(doc,anchor,label,'Caption',9.5,True);p.paragraph_format.keep_with_next=label.startswith('Table')
    r=p.add_run(body);r.font.name='Times New Roman';r.font.size=Pt(9.5);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    return p

def si_doc():
    d=Document(HERE/'Supporting_Information_revised.docx');anchor=find(d,'Declaration of AI-assisted manuscript preparation')
    h=before(d,anchor,'S8 Repeated common-test-set sensitivity','Heading 1',15,True);h.paragraph_format.page_break_before=True
    before(d,anchor,('To assess predictions on the same substrates in both catalyst systems, 20 distinct outer test sets per domain were sampled uniformly without replacement from the active ee-labelled cohorts using pseudorandom seeds 20261108 and 20261109. Six of 38 Fe(P7)Cl records or five of 26 Fe(CMC-Por)Cl records were held out per split and excluded from fitting and acquisition. The seven previously locked Fe(CMC-Por)Cl audit records remained excluded. Three distinct initial pairs were sampled from the remaining active candidates per split and shared across source-order continuation, uncertainty–diversity and random continuation; the random comparator was averaged over three independently seeded continuations per pair.'))
    before(d,anchor,('The existing representation, uncertainty–diversity scoring components, model settings, prediction bounds and training-only standardisation were retained. Ridge MAE on the common held-out records was averaged over 2, 6, 10, 15 and 20 active labels and then over the three starting pairs within each outer split. Paired differences are comparator minus uncertainty–diversity MAE; positive values favour uncertainty–diversity. The source-order continuation follows source order after the shared initial pair and is not the original archived source-order trajectory.'))
    add_caption(d,anchor,'Table S18. ','Repeated common-test-set sensitivity. A split effect is the average paired difference over three shared starting pairs and five label budgets. Random continuation is averaged over three continuations per starting pair. IQR is the interquartile range across the 20 split effects.')
    t=d.add_table(rows=1,cols=5);t.style='Table Grid';t.autofit=True;anchor._p.addprevious(t._tbl)
    for c,txt in zip(t.rows[0].cells,['Catalyst','Comparator','Mean difference\n(ee points)','Median (IQR)\n(ee points)','Splits favouring\nuncertainty–diversity']):
        cell_text(c,txt,True);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EDF2');c._tc.get_or_add_tcPr().append(sh)
    for row in [('Fe(P7)Cl','Source-order','2.85','2.28 (0.21 to 5.34)','17/20'),('Fe(P7)Cl','Random','0.37','0.50 (−1.17 to 1.19)','12/20'),('Fe(CMC-Por)Cl','Source-order','1.43','0.54 (−0.80 to 1.99)','11/20'),('Fe(CMC-Por)Cl','Random','1.06','0.27 (−0.02 to 2.37)','14/20')]:
        for c,txt in zip(t.add_row().cells,row):cell_text(c,txt)
    q=before(d,anchor,('The Fe(CMC-Por)Cl source-order mean is influenced by one split with a +17.76 ee-point difference; the split is retained and the median is 0.54. The observed source-order differences range from −2.45 to 9.28 for Fe(P7)Cl and −3.08 to 17.76 for Fe(CMC-Por)Cl. These results show variability across held-out sets rather than a uniform common-test advantage.'));q.paragraph_format.space_before=Pt(6)
    before(d,anchor,('For the average split-level source-order-minus-uncertainty–diversity difference, approximate 95% percentile intervals from 10,000 bootstrap resamples of the 20 split effects were 1.52 to 4.22 for Fe(P7)Cl and −0.06 to 3.48 for Fe(CMC-Por)Cl. Against random continuation the corresponding intervals were −0.60 to 1.49 and 0.41 to 1.77. These intervals summarise Monte Carlo variation under the selected split and starting-pair scheme conditional on the observed datasets; the test sets overlap and all models share the same small source datasets. The intervals are not confidence intervals across independently sampled substrates, experimental datasets or catalysts, and no population-level significance claim is made.'))
    before(d,anchor,('This analysis is distinct from the seven-record Fe(CMC-Por)Cl audit in Section S7 and from the original 55.3% and 33.2% trajectory-specific comparisons. It does not supply population-level confidence intervals for those original percentages. All split IDs, initial pairs, route selections, predictions, random seeds, input hashes and software versions are retained in the accompanying sensitivity-analysis records.'))
    pic=d.add_paragraph();anchor._p.addprevious(pic._p);pic.alignment=WD_ALIGN_PARAGRAPH.CENTER;pic.paragraph_format.keep_with_next=True;pic.add_run().add_picture(str(HERE/'results/common_test/common_test_split_differences.png'),width=Inches(6.2))
    add_caption(d,anchor,'Figure S10. ','Repeated common-test-set paired differences in mean ee MAE. Each point is one of 20 overlapping outer test splits; within each split, scores average three shared initial pairs and five label budgets. The random comparator averages three continuations per initial pair. Black bars show interquartile ranges and diamonds show medians. Positive comparator-minus-uncertainty–diversity values favour uncertainty–diversity. Splits are not independent datasets.')
    keep_captions_with_content(d);d.save(HERE/'Supporting_Information_common_test_revised.docx')

if __name__=='__main__':main_doc();si_doc()
