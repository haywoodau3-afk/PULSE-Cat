from pathlib import Path
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
p=Path(__file__).parent

def add_after(anchor, text):
    element=OxmlElement('w:p'); anchor._p.addnext(element)
    para=Paragraph(element,anchor._parent); para.style=anchor.style
    run=para.add_run(text); run.font.highlight_color=WD_COLOR_INDEX.YELLOW

def update(src,dst,needle,text):
    d=Document(p/src)
    matches=[x for x in d.paragraphs if needle in x.text]
    assert len(matches)==1
    add_after(matches[0],text)
    d.save(p/dst)
update('Manuscript_weight_sensitivity_revised.docx','Manuscript_comment2_closed.docx','In the 21-setting sensitivity grid,', 'Against the same held-out source-order continuation, mean paired differences favoured 21/21 weight settings for Fe(P7)Cl and 20/21 for Fe(CMC-Por)Cl, with one tie; against random continuation, they favoured 18/21 and 20/21 settings, respectively. These are descriptive averages over overlapping splits, with variation across individual splits (SI Section S9).')
update('Supporting_Information_weight_sensitivity_revised.docx','Supporting_Information_comment2_closed.docx','For Fe(P7)Cl, the default ranked 11th of 21', 'Each grid setting was also compared with the source-order and random continuations from Section S8 on the same held-out splits, starts, and budgets. Positive comparator-minus-setting differences favour the setting. Across the 21 settings, the mean difference versus source order was positive for 21 Fe(P7)Cl settings (range 1.28 to 3.38 ee points) and 20 Fe(CMC-Por)Cl settings (range 0.00 to 2.09; one setting tied on every split). Versus random, it was positive for 18 and 20 settings, respectively (ranges −1.20 to 0.90 and −0.37 to 1.72). Across individual settings, the number of the 20 splits favouring the setting ranged from 13 to 17 and 0 to 14 versus source order, and 8 to 15 and 11 to 17 versus random, respectively. The full grid comparisons are provided in the accompanying analysis files. These means describe the fixed datasets and overlapping splits; they do not establish statistical significance or general superiority. The saved weight-grid outputs contain common-test predictions at five budgets, not remaining-pool predictions for every prefix; they cannot reconstruct the original mean-prefix metric.')
