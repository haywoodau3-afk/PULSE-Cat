from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
from pathlib import Path
P=Path(__file__).resolve().parent
src=P.parent/'reviewer2_comment1'

def before_first(doc,text):
    p=doc.paragraphs[0].insert_paragraph_before()
    r=p.add_run(text);r.bold=True;r.font.color.rgb=RGBColor(0xB0,0,0);r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    return p

def add_after(p,text='',bold=False):
    new=OxmlElement('w:p');p._p.addnext(new);q=Paragraph(new,p._parent)
    r=q.add_run(text);r.bold=bold;r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    return q

def highlighted(p,text):
    r=p.add_run(text);r.font.highlight_color=WD_COLOR_INDEX.YELLOW

def replace_paragraph(p,text):
    p.clear();highlighted(p,text)

warning='WORKING DRAFT — NOT FOR SUBMISSION. A substrate atom-index error was found in the original pose-feature calculation. Pose-dependent results, figures and prior reviewer responses are being reanalysed and must not be relied upon until independently checked and reconciled.'
d=Document(src/'Manuscript_reviewer2_comment1_closed.docx');before_first(d,warning)
for p in d.paragraphs:
    if p.text.startswith('A substrate, rather than an individual pose, is the statistical observation.'):
        replace_paragraph(p,'A substrate, rather than an individual pose, is the statistical observation; all its poses remain in the same split. In the original 38-substrate representation benchmark, constant features were removed globally without using labels before the held-out splits, whereas standardisation was fitted on each training split. For the corrected Elastic Net fits, a check using training-only constant-feature filtering with the same selected hyperparameters reproduced the held-out predictions; other model-selection and estimator results require separate verification.')
        break
anchor=next(p for p in d.paragraphs if p.text.startswith('These results illustrate an important distinction'))
p=add_after(anchor,'Illustrative substrate examples',True)
p=add_after(p,'The reported Fe(P7)Cl examples 1a and 1ah share the aryl azide and initial two-carbon tether but differ at the carbon that becomes stereogenic: 1a bears a phenyl substituent and 1ah an ethyl substituent. Under the reported 60 °C conditions, their products 2a and 2ah gave 92% and 50% ee, respectively. The substitution changes both steric and electronic properties as well as accessible conformations, so these observations do not identify the cause of the ee difference.')
p=add_after(p,'Using corrected pose features, the target-held-out structure-only model predicted 81.0% and 73.2% ee, and the corresponding structure-plus-pose model predicted 90.2% and 58.7% ee, respectively. These examples illustrate a closer numerical fit for the two selected substrates, not independent validation. Across 200 sampled poses per substrate, the mean substrate-centroid-to-Fe distances were 4.515 and 3.869 Å, and the mean nitrene-N-to-reactive-carbon distances were 3.460 and 3.582 Å, respectively. These descriptors differ between the examples, but their fitted coefficients were zero in both example-specific target-held-out pose models; the predictions therefore cannot be attributed directly to either descriptor. The centroid measure also depends on molecular size and atom count. The displayed poses are sampled structures, not established transition states or experimental conformational populations (SI Section S16).')
img=add_after(p);img.paragraph_format.page_break_before=True
img.add_run().add_picture(str(P/'results/substrate_examples.png'),width=Inches(6.15))
p=add_after(img,'Figure X. Two Fe(P7)Cl substrate examples. The 2D structures show starting azides; the 3D views show the lowest-scoring retained UFF iron-bound nitrene assembly for each substrate, with a common frozen catalyst core and proximal catalyst atoms displayed. Green marks the reported reactive carbon, blue the nitrene nitrogen, and orange iron. Reported ee values are for products 2a and 2ah; predictions use target-held-out models. Single sampled poses do not establish a mechanism or ensemble populations. Figure numbering is provisional.')
p.paragraph_format.keep_with_next=False
d.save(P/'Manuscript_reviewer2_comment2_PROVISIONAL.docx')

s=Document(src/'Supporting_Information_reviewer2_comment1_closed.docx');before_first(s,warning)
for p in s.paragraphs:
    if p.text.startswith('A substrate, not a pose, is the statistical observation.'):
        replace_paragraph(p,'A substrate, not a pose, is the statistical observation, and all its poses remain in the same split. The original 38-substrate representation benchmark applied a label-blind global constant-feature filter before splitting; training-fold scaling and model fitting were then performed within each split. With the already selected Elastic Net hyperparameters, a separate training-only constant-feature-filter check reproduced all 76 corrected target- and family-held-out pose predictions to numerical precision. This check does not establish equivalence for hyperparameter selection or other estimators.')
        break
p=s.add_paragraph();highlighted(p,'S16 Illustrative substrate structures and corrected descriptor audit');p.runs[0].bold=True
for txt in [
 'The examples were selected from the Fe(P7)Cl cohort because source Table 1 reports 1a → 2a and 1ah → 2ah at 60 °C with 92% and 50% ee and a shared scaffold. The phenyl-to-ethyl change also changes other molecular properties, preventing causal attribution of the ee difference. Selection preceded inspection of model coefficients. The 2D files are editable molecular structure files; no native ChemDraw format is claimed.',
 'For each substrate the figure displays the rank-1 retained UFF assembly (1a: stage1-smoke-1a-substrate-uff-0001; 1ah: stage1-smoke-1ah-substrate-uff-0001). The original 214-atom frozen catalyst core is common; only proximal core atoms are drawn. The structures are sampled iron-bound nitrene assemblies; the 2D structures are the starting azides. These are illustrative structures, not verified transition states, experimentally determined structures, or equilibrium conformer populations.',
 'The mean substrate-heavy-atom centroid-to-Fe distances across 200 retained poses are 4.515124 Å (1a) and 3.869390 Å (1ah); corresponding mean nitrene-nitrogen-to-reported-reactive-carbon distances are 3.460454 and 3.581514 Å. The centroid depends on molecular size and composition. Independent recalculation from the 200 archived coordinates exposed an incorrect original atom-index assumption for suffix-style nitrene SMILES, which has been corrected for these reanalyses. Other pose-dependent results remain subject to reconciliation.',
 'For 1a and 1ah, respectively, target-held-out structure-only Elastic Net predictions were 81.0 and 73.2% ee; corrected structure-plus-pose predictions were 90.2 and 58.7% ee. The two displayed descriptors have zero coefficients in each target-held-out fitted model, and also in each corresponding family-held-out model. Thus the fitted models do not directly use these individual descriptors for these predictions; different descriptors may contribute. The two examples were not independently selected for external validation.',
 'Reproducible coordinates, 2D structure files, feature values, checks and corrected predictions are recorded in the Reviewer 2 comment 2 working folder. The source audit also preserves archived pre-correction predictions; use corrected_example_details.json for corrected pose predictions. The companion data package and all prior reviewer-response analyses are provisional pending complete regeneration, independent validation, and consistent revision of the manuscript, figures, SI and data release.'
]:
 p=s.add_paragraph();highlighted(p,txt)
s.save(P/'Supporting_Information_reviewer2_comment2_PROVISIONAL.docx')
