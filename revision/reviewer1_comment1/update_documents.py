#!/usr/bin/env python3
"""Apply the recorded reviewer 1 comment 1 results to separate DOCX copies."""
from copy import deepcopy
from pathlib import Path
from docx import Document
from docx.text.run import Run
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

HERE=Path(__file__).resolve().parent
REV=HERE.parent

def replacement(p,old,new):
    text=''.join(r.text for r in p.runs)
    assert text.count(old)==1,(old[:100],text.count(old))
    start=text.index(old);end=start+len(old);offset=0;affected=[]
    for r in p.runs:
        a=offset;b=a+len(r.text);offset=b
        if b>start and a<end:affected.append((r,a,b,r.text))
    assert affected
    first,fa,fb,ft=affected[0];last,la,lb,lt=affected[-1]
    prefix=ft[:max(0,start-fa)];suffix=lt[max(0,end-la):]
    if first is last:
        first.text=prefix
        replacement_element=deepcopy(first._r);first._r.addnext(replacement_element)
        inserted=Run(replacement_element,p);inserted.text=new;inserted.font.highlight_color=WD_COLOR_INDEX.YELLOW
        if suffix:
            suffix_element=deepcopy(first._r);replacement_element.addnext(suffix_element);Run(suffix_element,p).text=suffix
    else:
        first.text=prefix
        for run,_,_,_ in affected[1:-1]:run.text=''
        last.text=suffix
        element=deepcopy(first._r);first._r.addnext(element)
        inserted=Run(element,p);inserted.text=new;inserted.font.highlight_color=WD_COLOR_INDEX.YELLOW
    assert new in p.text

def insert_after(doc,anchor,text,style='Normal'):
    p=doc.add_paragraph(style=style);anchor._p.addnext(p._p)
    r=p.add_run(text);r.font.name='Times New Roman';r.font.size=Pt(11);r.font.color.rgb=RGBColor(0,0,0);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    return p

def before(doc,anchor,text,style='Normal',size=11,bold=False):
    p=doc.add_paragraph(style=style);anchor._p.addprevious(p._p)
    r=p.add_run(text);r.font.name='Times New Roman';r.font.size=Pt(size);r.bold=bold;r.font.color.rgb=RGBColor(0,0,0);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    return p

def keep_captions_with_content(doc):
    for p in doc.paragraphs:
        if p.style.name!='Caption':continue
        if p.text.startswith('Table '):p.paragraph_format.keep_with_next=True
        elif p.text.startswith('Figure '):
            prev=p._p.getprevious()
            if prev is not None and prev.tag==qn('w:p') and prev.xpath('.//w:drawing'):
                Paragraph(prev,p._parent).paragraph_format.keep_with_next=True

def main_document():
    d=Document(REV/'Manuscript.docx');p=d.paragraphs
    p[54].paragraph_format.keep_with_next=True  # keep Figure 3 with its caption after text reflow
    old='In matched progressive-learning comparisons, uncertainty–diversity ordering reduced mean-prefix enantiomeric-excess error by 55.3% and 33.2% relative to reported substrate order for Fe(P7)Cl and Fe(CMC-Por)Cl, respectively, and outperformed diversity-first, random, and performance-first selection.'
    new='In two archived comparisons with different initial substrate pairs, uncertainty–diversity reduced mean-prefix enantiomeric-excess error by 55.3% and 33.2% relative to source order for Fe(P7)Cl and Fe(CMC-Por)Cl, respectively. In a shared-start sensitivity analysis it gave lower remaining-pool error than source-order continuation for 50/50 and 45/50 sampled starting pairs; a seven-substrate fixed audit for Fe(CMC-Por)Cl gave mixed results.'
    replacement(p[5],old,new)
    replacement(p[5],'These results show that catalyst-contextual representation and substrate order can each increase the information extracted from small catalytic datasets while addressing distinct aspects of model development.','These results suggest that catalyst-contextual representation and substrate order can affect information extracted from small catalytic datasets, subject to the evaluation and starting-scope limitations.')
    replacement(p[48],'The independent robustness analysis uses a separately documented progression protocol and evaluates multiple estimators using trajectory-level AUC-MAE.','The independent robustness analysis uses a separately documented progression protocol and evaluates multiple estimators using trajectory-level AUC-MAE. The archived source-order and uncertainty–diversity trajectories began with 1a/1b and 1a/1am for Fe(P7)Cl, respectively, and 2aa/2ab and 2b/2ac for Fe(CMC-Por)Cl.')
    insert_after(d,p[50],('To examine starting-scope sensitivity, 50 distinct initial substrate pairs per catalyst were sampled uniformly without replacement using fixed pseudorandom seeds. Source-order continuation, uncertainty–diversity, and three random continuations per pair used the same initial two substrates and label budgets. The primary summary was Ridge mean-prefix MAE on each route’s remaining active pool. Paired differences were summarised across starting pairs, with 10,000 pair-level bootstrap resamples for approximate 95% intervals for their mean. These intervals describe the sampled starting-pair distribution conditional on the observed datasets, not uncertainty over new substrates or catalysts. A secondary Fe(CMC-Por)Cl analysis evaluated seven previously locked ee-labelled substrates at 6, 13, and 20 active labels; their three MAEs were averaged within each route and starting pair (SI Section S7).'))
    replacement(p[64],'It also outperformed diversity-first, random, and performance-first selection in both matched comparisons.','In these recorded comparisons it also gave lower error than diversity-first, the averaged random comparator, and performance-first selection. These two trajectory comparisons do not themselves quantify uncertainty across initial pairs.')
    replacement(p[65],'These comparisons support an information-selection effect within the available substrate sets.','These comparisons describe information-selection effects within the two available retrospective substrate sets.')
    replacement(p[65],'The resulting reductions quantify how substrate ordering affected retrospective model error as labels accumulated, while prospective validation is needed to establish the corresponding effect on experimental effort.','Because the original routes also began with different substrate pairs, the reductions combine starting-scope and subsequent ordering effects; prospective validation is needed to establish any effect on experimental effort.')
    q=insert_after(d,p[65],('Across 50 shared starting pairs, uncertainty–diversity had lower mean-prefix MAE than source-order continuation for 50/50 Fe(P7)Cl pairs and 45/50 Fe(CMC-Por)Cl pairs. The mean paired source-order-minus-uncertainty–diversity differences were 6.14 ee points (conditional 95% pair-bootstrap interval 5.41 to 6.88) and 1.66 ee points (1.27 to 2.04), respectively. Against the mean of three random continuations per starting pair, uncertainty–diversity had lower error for 31/50 and 47/50 pairs, respectively. The route-specific remaining pools differ as selection proceeds, and these intervals do not quantify substrate- or catalyst-population uncertainty (Table S17 and Fig. S8).'))
    insert_after(d,q,('The fixed-test-set check gives a more limited result. For the seven previously locked Fe(CMC-Por)Cl ee records, the mean paired source-order-minus-uncertainty–diversity MAE across 6, 13 and 20 active labels was −0.40 ee points (conditional 95% pair-bootstrap interval −1.02 to 0.20); uncertainty–diversity had lower error for 27/50 starting pairs. Thus the remaining-pool advantage did not translate into a consistent advantage on this small fixed audit set. The Fe(P7)Cl late-stage records lack measured ee and could not provide an analogous labelled audit.'))
    replacement(p[68],'The result is therefore robust across several estimator/domain combinations but is not universal (Table 3 and Fig. 5).','The recorded result is consistent across several estimator/domain combinations but is not universal; these fixed-start trajectories do not establish across-start uncertainty (Table 3 and Fig. 5).')
    replacement(p[88],'sensitivity to the exact initial measured panel has not been exhaustively characterised','sensitivity to initial pairs has been examined only in the two observed datasets and has not been exhaustively characterised for broader starting panels')
    replacement(p[88],'testing acquisition robustness to different starting scopes','testing acquisition robustness across additional datasets and larger starting scopes')
    replacement(p[90],'while information-guided ordering lowered retrospective learning error in both studied systems.','while information-guided ordering often lowered remaining-pool error relative to source-order continuation across sampled starts; the small fixed Fe(CMC-Por)Cl audit did not show a consistent advantage.')
    keep_captions_with_content(d);d.save(HERE/'Manuscript_revised.docx')

def cell_text(cell,text,bold=False):
    p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1
    r=p.add_run(str(text));r.font.name='Times New Roman';r.font.size=Pt(8.5);r.bold=bold;r.font.highlight_color=WD_COLOR_INDEX.YELLOW

def si_document():
    d=Document(REV/'Supporting_Information.docx');p=d.paragraphs
    insert_after(d,p[133],('A current-code replay reproduced every recorded Ridge prefix MAE and the complete source-order and uncertainty–diversity selection sequences for both domains. This numerical agreement does not establish the original execution environment or every archived output. Section S7 reports a separate shared-start sensitivity analysis and a fixed Fe(CMC-Por)Cl audit.'))
    anchor=p[242]
    heading=before(d,anchor,'S7 Shared-start acquisition sensitivity and fixed audit','Heading 1',15,True);heading.paragraph_format.page_break_before=True
    before(d,anchor,('Fifty distinct unordered initial pairs were sampled uniformly without replacement from the 38 Fe(P7)Cl and 26 Fe(CMC-Por)Cl active ee-labelled substrates using pseudorandom seeds 20261105 and 20261106, respectively. Each pair was used for both uncertainty–diversity and source-order continuation; the latter selected the earliest remaining source-order record after the common starting pair. Three independently seeded random continuations were also evaluated per pair and their mean used as the random comparator. All routes retained the existing rdkit_morgan_stage2p representation, model settings, prediction bounds and training-only preprocessing; uncertainty–diversity retained its original acquisition score. Ridge MAE was evaluated on each route’s unrevealed active pool at nonempty prefixes 2–37 and 2–25, respectively, then averaged over prefixes.'))
    before(d,anchor,('For each initial pair, the paired difference is comparator mean-prefix MAE minus uncertainty–diversity mean-prefix MAE; positive values favour uncertainty–diversity. The approximate 95% intervals in Table S17 are percentile intervals for the mean paired difference from 10,000 resamples of the 50 pair-level differences. They describe variation in the mean over the sampled starting-pair distribution conditional on the observed datasets and protocol. They are not confidence intervals for the original two single-trajectory reductions or for a population of substrates, experimental outcomes or catalysts. Initial pairs were sampled without replacement from finite sets; the simple bootstrap does not apply a finite-population correction. No formal significance test is claimed.'))
    cap=before(d,anchor,'Table S17. ','Caption',9.5,True);cap.paragraph_format.keep_with_next=True
    r=cap.add_run('Shared-start sensitivity of mean-prefix ee MAE. Positive comparator-minus-uncertainty–diversity differences favour uncertainty–diversity. Random continuation is averaged over three continuations per starting pair.');r.font.name='Times New Roman';r.font.size=Pt(9.5);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    t=d.add_table(rows=1,cols=5);t.style='Table Grid';t.autofit=True;anchor._p.addprevious(t._tbl)
    headers=['Catalyst','Comparator','Mean difference\n(ee points)','Conditional 95%\ninterval','Pairs favouring\nuncertainty–diversity']
    for c,txt in zip(t.rows[0].cells,headers):
        cell_text(c,txt,True);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EDF2');c._tc.get_or_add_tcPr().append(sh)
    data=[('Fe(P7)Cl','Source-order','6.14','5.41 to 6.88','50/50'),('Fe(P7)Cl','Random','0.50','0.15 to 0.86','31/50'),('Fe(CMC-Por)Cl','Source-order','1.66','1.27 to 2.04','45/50'),('Fe(CMC-Por)Cl','Random','2.62','2.13 to 3.11','47/50')]
    for row in data:
        cells=t.add_row().cells
        for c,txt in zip(cells,row):cell_text(c,txt)
    pafter=before(d,anchor,('The mean paired differences versus source-order continuation are 6.14 and 1.66 ee points for Fe(P7)Cl and Fe(CMC-Por)Cl, respectively. Against random continuation they are 0.50 and 2.62 ee points. In Fe(P7)Cl, uncertainty–diversity is lower than the random-continuation mean in 31/50 pairs, illustrating substantial starting-pair variation. At each prefix the remaining pool is route-specific, so these comparisons are not evaluations on a common test set.'));pafter.paragraph_format.space_before=Pt(6)
    before(d,anchor,('For a prespecified secondary check, the same 50 Fe(CMC-Por)Cl starting pairs were evaluated on the seven previously locked ee-labelled records 2y, 2z and 4a–4e, which were excluded from the active pool. Ridge audit MAE was computed at 6, 13 and 20 active labels and averaged over those budgets. The mean source-order-minus-uncertainty–diversity difference was −0.40 ee points (conditional pair-bootstrap 95% interval −1.02 to 0.20), and 27/50 pairs favoured uncertainty–diversity. This small fixed set does not establish a consistent held-out advantage and is not a fresh prospective external validation. Fe(P7)Cl late-stage records lack measured ee and cannot serve as a labelled common test set.'))
    pic=d.add_paragraph();anchor._p.addprevious(pic._p);pic.alignment=WD_ALIGN_PARAGRAPH.CENTER;pic.paragraph_format.keep_with_next=True;pic.add_run().add_picture(str(HERE/'results/shared_start_sensitivity.png'),width=Inches(6.2))
    cap=before(d,anchor,'Figure S8. ','Caption',9.5,True)
    r=cap.add_run('Shared-start sensitivity of remaining-pool mean-prefix ee MAE. Each point is one of 50 initial substrate pairs; the black bar shows the interquartile range and the diamond the median. Positive comparator-minus-uncertainty–diversity values favour uncertainty–diversity. The random comparator averages three continuations from the same initial pair. Routes can have different remaining evaluation pools. The seven-record fixed Fe(CMC-Por)Cl audit is a separate check described above.');r.font.name='Times New Roman';r.font.size=Pt(9.5);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    pic=d.add_paragraph();anchor._p.addprevious(pic._p);pic.alignment=WD_ALIGN_PARAGRAPH.CENTER;pic.paragraph_format.keep_with_next=True;pic.add_run().add_picture(str(HERE/'results/shared_start_learning_curves.png'),width=Inches(6.2))
    cap=before(d,anchor,'Figure S9. ','Caption',9.5,True)
    r=cap.add_run('Remaining-pool ee MAE at each nonempty prefix. Solid lines show the medians over 50 shared starting pairs and shaded bands show the interquartile ranges; dashed lines show the two original archived trajectories, which used route-specific initial pairs. These bands describe variation across the sampled starting pairs and are not confidence intervals. Each route has its own evolving remaining evaluation pool.');r.font.name='Times New Roman';r.font.size=Pt(9.5);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    before(d,anchor,('The accompanying sensitivity-analysis records retain initial-pair IDs, random seeds, per-prefix results, fixed-audit predictions, input hashes, package versions and replay scripts. Original archived results were not overwritten. Elastic Net convergence warnings are suppressed by the original scoring code; their absence does not establish that every fit converged.'))
    keep_captions_with_content(d);d.save(HERE/'Supporting_Information_revised.docx')

if __name__=='__main__':main_document();si_document()
