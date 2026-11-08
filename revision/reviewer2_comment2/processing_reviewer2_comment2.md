# Reviewer 2, comment 2: Substrate examples and descriptor interpretation

## Reviewer comment

Could the author discuss two representation substrate examples (with chemdraw and 3D structure) to illustrate how changes in sterics or conformation affect ee, and whether these trends are captured by their descriptors? I think in that way, this paper can be better appreciated by organic chemistry community.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**2.1 Catalytic chemistry — paragraph 18**

> The experimental basis comprises two independently published iron-porphyrin scopes. Lee and co-workers reported Fe(P7)Cl-catalysed asymmetric C–H amination, while Wang and co-workers reported visible-light-driven Fe(CMC-Por)Cl catalysis.[19,20] In both systems, a tethered organic azide undergoes intramolecular C(sp3)–H amination with loss of dinitrogen to form an enantioenriched N-heterocyclic product. The source studies report enantiomeric excess and isolated yield. Curated records retain starting-azide identity, product identity where reported, the experimentally assigned reactive site, measured outcomes, chemical-family labels, source order, and literature provenance. Thus, the chemistry considered here is a specific scope-learning problem for intramolecular nitrene transfer, rather than a general dataset of iron-catalysed C–H functionalisation.

**2.1 Catalytic chemistry — paragraph 19**

> The principal literature conditions also distinguish the two domains. The Fe(P7)Cl scope used 2 mol% catalyst in diethyl ether at 60 °C for 18 h with 4 Å molecular sieves, with selected less reactive substrates examined at 80 or 100 °C.[19] The principal aryl-azide protocol for Fe(CMC-Por)Cl used 2 mol% catalyst and di-tert-butyl dicarbonate in toluene under 410 nm irradiation at -10 °C.[20] That study includes both aryl azides forming indolines and arylsulfonyl azides forming cyclic sulfonamides, with substrate-class-specific protocol differences. These conditions describe the source datasets; no literature reactions were repeated in the present study. The transformation and catalyst structures are summarised in Fig. 1.

**2.1 Catalytic chemistry — paragraph 21**

> Figure 1. Catalytic systems and transformation studied. The scheme summarises the reported intramolecular C(sp3)–H amination of tethered azides and the two independently reported iron-porphyrin catalysts; substrate-specific structures and conditions remain documented in the source studies and SI.

**2.3 Endpoints and curation — paragraph 27**

> The principal selectivity endpoint is the magnitude of reported enantiomeric excess; signed stereochemical direction is not modelled. Because the target is |ee|, the present models predict the strength of stereochemical discrimination rather than its direction. Substrates giving equal-magnitude but opposite enantiomeric preferences are therefore equivalent under this target, and prospective prediction of absolute stereochemical preference would constitute a distinct modelling problem. Isolated yield is analysed separately rather than combined with ee into a composite outcome. Missing ee is not interpreted as zero and is not replaced by yield. Conversely, an experimentally measured zero-ee result remains a valid observation. Missing or unreported outcomes are retained as missing and are not assigned failure labels. The curation specification also preserves starting-material azide SMILES, free-nitrene structures used for pose construction, product SMILES when reported, reactive-site atom maps, family and scaffold groups, exclusions, source order, and provenance. Full row-level definitions and reconciliation of the analysis-specific populations are provided in SI Section S1.

**3.1 PULSE-Pose molecular representation — paragraph 32**

> Structure-only descriptors and fingerprints encode connectivity and physicochemical properties.[27,28] PULSE-Pose is conceptually inspired by SMART/SMARTpy catalyst-cavity descriptors, which use spatial probes to characterise reactive-pocket constraints.[25,26] Here, catalyst context is introduced by embedding substrate conformations relative to a fixed catalyst environment and summarising accessibility around the reported reactive site. This complements, rather than replaces, structure-only molecular representations and established 3D-QSAR approaches.

**3.1 PULSE-Pose molecular representation — paragraph 33**

> Baseline molecular inputs are sanitised starting-material azide SMILES. Compact RDKit physicochemical descriptors and radius-2 binary Morgan fingerprints encode size, lipophilicity, polarity, flexibility, ring content, heteroatom content, and local connectivity.[27,29] Outcome values, catalyst identity, source order, and family or scaffold labels are excluded from the molecular predictor columns. The complete descriptor list and fingerprint dimensions remain in SI Section S2.

**3.1 PULSE-Pose molecular representation — paragraph 34**

> Pose construction begins from the corresponding free-nitrene structure with explicit hydrogens. ETKDGv3 generates conformers, which are relaxed with UFF and aligned through the nitrene nitrogen and its bonded neighbour into a fixed catalyst reference frame.[30,31,32] Catalyst coordinates remain rigid. Candidates must preserve connectivity, complete optimisation, and pass a catalyst–substrate clash screen in which the intended Fe–N(nitrene) distance is exempted from the general clash criterion. Valid geometries are ranked by UFF score, and non-overlapping low- and high-ranked strata are retained. The high-ranked stratum is retained as a geometric-contrast representation rather than as a putative thermodynamic population; differences between strata are intended to capture configurational sensitivity of the catalyst-referenced descriptor space. No ee or yield is used during conformer generation, alignment, screening, ranking, or retention. This procedure is rigid catalyst-referenced assembly and screening, not optimisation of a complete catalyst–substrate complex; thresholds, radii, seeds, and acceptance checks remain fully specified in SI Section S2.

**3.1 PULSE-Pose molecular representation — paragraph 35**

> The Stage-2p representation contains 248 fields organised by chemical function rather than treated as an uninterpreted descriptor block. These include radial and angular spatial distributions around the nitrene and transferred-hydrogen anchors, directed geometry along the reported N–H–C reaction corridor, corridor occupancy, symmetry and stratum-contrast summaries, relational distribution features, and compact catalyst-interaction or pocket-crowding quantities. Distributional kernels, equations, field ordering, and selected-column manifests are retained in the SI and computational release.

**3.1 PULSE-Pose molecular representation — paragraph 36**

> The reactive-site atom map is taken from the reported chemistry. PULSE-Pose is therefore a site-conditioned retrospective representation rather than a prospective reaction-site or site-selectivity model. The retained UFF-ranked geometries are sampled configurations, not transition states, free-energy populations, Boltzmann ensembles, or mechanistically assigned conformers.

**4.1 Catalyst-referenced representations — paragraph 54**

> In the matched 38-substrate Fe(P7)Cl comparison (Fig. 3), adding selected pose descriptors to the structure-only Elastic Net model reduced target-held-out MAE from 12.612 to 8.583 ee percentage points, a 31.9% reduction. With complete families withheld, MAE decreased from 10.406 to 9.334, a smaller 10.3% improvement.

**4.1 Catalyst-referenced representations — paragraph 56**

> Figure 3. Selected catalyst-referenced descriptors improve prediction in the matched 38-substrate Fe(P7)Cl comparison using Elastic Net. Errors are ee percentage points. Target- and family-held-out validation answer different questions; SI Section S3 provides full metrics and split definitions.

**4.1 Catalyst-referenced representations — paragraph 57**

> The smaller family-held-out improvement indicates that catalyst-referenced geometry supplies useful information within the studied chemical domain but is less powerful when extrapolating across complete substrate families. The two protocols therefore support different levels of inference: the target-held-out result quantifies interpolation among represented chemistry, whereas the family-held-out result provides the more demanding test of transfer across family boundaries.

**4.1 Catalyst-referenced representations — paragraph 58**

> Larger spatial representations did not automatically improve prediction. Adding 655 occupancy and flexibility fields to the corresponding local-geometry reference worsened MAE from 10.281 to 14.132 ee points and changed R² from 0.311 to -0.175. Later descriptor additions produced only small or inconsistent changes across MAE, RMSE, and R² (SI Section S3). The observed pose benefit is therefore not explained simply by increasing descriptor dimensionality.

**4.1 Catalyst-referenced representations — paragraph 59**

> Isolated-substrate conformational and electronic additions also failed to improve the separately locked nested-family reference. MAE was 8.498 for the locked 248-field geometry, 8.858 after adding CREST geometry, 8.610 after adding GFN2-xTB electronic features, and 8.876 with both blocks.[36,37] No addition improved MAE, RMSE, or R². This comparison does not imply that CREST or GFN2-xTB are generally inferior; rather, isolated-substrate conformational or electronic information was insufficient to replace the catalyst-contextual representation in this dataset.

**4.1 Catalyst-referenced representations — paragraph 60**

> These results illustrate an important distinction between descriptor richness and usable information in the small-data regime. A representation can contain chemically meaningful spatial, conformational, or electronic quantities without improving prediction if the number of labelled substrates is insufficient to estimate their contributions reliably. Increasing representation dimensionality can therefore add variance, redundancy, or poorly constrained correlations rather than predictive information. The design objective is to identify representations that express chemically relevant distinctions at a complexity commensurate with the available data. In this sense, molecular representation and experimental acquisition address the same underlying limitation from opposite directions: one determines which information is encoded from each substrate, while the other determines which substrates are measured to provide that information.

**4.1 Catalyst-referenced representations — paragraph 61**

> Thirteen exact canonical aryl identities were shared between the catalyst domains. The Fe(P7)Cl 1i/Fe(CMC-Por)Cl 2r pair in Fig. 4 was selected because it had the largest occupancy divergence among those pairs. Substantial overlap nevertheless remained, including a Bhattacharyya overlap of 0.9618 for the compared normalised fields. The example illustrates catalyst-dependent reshaping of sampled occupancy, not complete relocation or mechanistic proof of selectivity.

**4.1 Catalyst-referenced representations — paragraph 63**

> Figure 4. Catalyst-referenced PULSE-Pose ensembles for shared-substrate records Fe(P7)Cl 1i and Fe(CMC-Por)Cl 2r. This maximum-divergence example among 13 shared identities retains substantial occupancy overlap; the poses are sampled geometries, not mechanistic populations (SI Section S2).

**4.3 Information content of molecular representations — paragraph 80**

> Representation is a chemical design choice encompassing both information content and computational complexity.[39] The occupancy and CREST/GFN2-xTB ablations show that adding more spatial, conformational, or electronic variables does not automatically improve prediction. Catalyst-contextual descriptors allow chemists to encode system-specific information and test its predictive value,[25,26,40] consistent with the broader use of steric and electrostatic descriptors in catalyst-library screening.[41]

**4.3 Information content of molecular representations — paragraph 81**

> PULSE-Pose shares with CoMFA and other 3D-QSAR approaches the premise that spatial organisation can contain predictive selectivity information. Its purpose is narrower: rather than deriving a general field around an isolated ligand or substrate, it constructs an ensemble of substrate geometries in a specified catalyst reference frame and summarises that ensemble for small-data prediction. It should therefore be interpreted as a predictive catalyst-context representation, not as a mechanistic transition-state model.

**4.3 Information content of molecular representations — paragraph 82**

> The present representation assumes a reported reactive site. Reactions with multiple unknown competing sites would require candidate-site enumeration or an upstream site-selectivity model before this workflow could be applied prospectively. The results therefore test substrate-scope learning conditional on a known reaction-site assignment.

**4.4 From retrospective analysis to experimental scope design — paragraph 88**

> Transferability should therefore be considered separately for the representation and acquisition components. Catalyst-referenced descriptors such as PULSE-Pose are intrinsically dependent on the geometry and chemistry of the catalytic environment; extension to a different catalyst or transformation may require redefining the reactive frame, interaction features, or conformational treatment. PULSE-Acquire, by contrast, operates at a more abstract experimental-design level and may not require the same molecular representation to be retained. Its broader principle—balancing what the model does not yet know with what regions of chemical space remain poorly represented—could be implemented using different reaction-appropriate descriptors, uncertainty estimates, and chemical groupings. Future cross-reaction studies should therefore distinguish representation transfer, in which a molecular encoding remains predictive in a new system, from acquisition transfer, in which an information-guided selection strategy remains beneficial after the representation and acquisition components have been adapted to the new chemistry. The present work establishes neither form of transfer across unrelated catalytic classes.

**4.4 From retrospective analysis to experimental scope design — paragraph 89**

> The principal limitations accordingly apply to both components of the framework. For PULSE-Pose, the present analysis assumes a known reactive site and a fixed catalyst reference geometry; substantially flexible catalysts or reactions with competing unknown sites may require catalyst-ensemble sampling, joint catalyst–substrate conformational treatment, or an upstream site-selectivity model. For PULSE-Acquire, the analyses remain retrospective, different acquisition routes can leave different remaining prediction pools, sensitivity to the exact initial measured panel has not been exhaustively characterised, and the preferred policy is not universal across estimators or endpoints. No prospective laboratory loop or cross-reaction validation is reported. These boundaries define the next validation tasks: testing acquisition robustness to different starting scopes, determining whether acquisition rules require system-specific recalibration, evaluating chemically distinct catalyst families, and ultimately measuring whether information-guided substrate selection improves prospective experimental scope construction.

### Supporting information

**S1.1.1 Reaction sources and curation — paragraph 13**

> The experimental domains are Fe(P7)Cl and Fe(CMC-Por)Cl intramolecular C(sp3)–H amination, as reported independently by Lee and co-workers and Wang and co-workers, respectively [1,2]. The curation specification records reaction and substrate identifiers, catalyst and condition identifiers, starting-material azide SMILES, free-nitrene SMILES, product SMILES when reported, reactive-site atom maps, experimental ee/yield, family and scaffold groups, exclusions, source order, and provenance. Missing product structures remain null rather than being computationally reconstructed. Missing ee is not zero and is not replaced by yield. A measured zero-ee outcome remains a valid observation; an unreported reaction is not assigned a failure label.

**S1.1.1 Reaction sources and curation — paragraph 14**

> Canonical matching removes atom-map labels before RDKit canonicalisation [3]. The 13 canonical aryl substrates shared between the domains are identified in the overlap ledger. They define the eligible population for paired geometry diagnostics. The release inventory locates the row-level ledgers and source links under curated-datasets/; see Section S5.1.

**S2 PULSE-Pose construction and molecular representations — paragraph 20**

> Figure S1. Contextual molecular-representation approaches from the source framework illustration: graph neural networks, CREST conformational exploration, and SMART catalyst-cavity descriptors. This is methodological context, not a head-to-head benchmark in this study.[4,5,6]

**S2.1 Molecular connectivity and feature definitions — paragraph 22**

> Molecular inputs are sanitised starting-material azide SMILES. Missing or unparsable SMILES and duplicate substrate identifiers stop feature-table construction. Outcome, catalyst, source-order, and grouping metadata are not molecular predictor columns. Morgan bit vectors follow circular-fingerprint methodology [7]. B3–B5 use radius 2, binary rather than count fingerprints, and includeChirality=False.

**S2.1 Molecular connectivity and feature definitions — paragraph 23**

> The 15 RDKit descriptors, in the documented column order, are heavy-atom count, molecular weight, Crippen logP [8], topological polar surface area [9], formal charge, fraction of sp3 carbon, rotatable-bond count, total ring count, aromatic-ring count, hydrogen-bond acceptor count, hydrogen-bond donor count, heteroatom count, aliphatic-ring count, spiro-atom count, and tetrahedral chiral-centre count. The last counts assigned and unassigned centres through Chem.FindMolChiralCenters(includeUnassigned=True); it is not an absolute-configuration encoding. B1 retains molecular weight, logP, polar surface area, fraction sp3, rotatable bonds, and total rings.

**S2.1 Molecular connectivity and feature definitions — paragraph 26**

> C1 contains 44 retained geometry summaries; C2 contains 16 explicit catalyst-interaction summaries. Their functional categories include attack-corridor geometry, directed fields, stratum contrasts/stability, catalyst contacts, pocket crowding, and corridor obstruction. Exact selected column names are referred to the released feature manifests, data dictionary, and feature source described in Section S5.5. Repeated numeric interaction values are averaged by substrate before selecting C2; missing required interactions cause failure, not zero imputation. A separate legacy candidate-site builder uses a chirality-aware 2,048-bit fingerprint and is not B5. Literature on cavity descriptors motivates catalyst-aware representations but does not validate this study's feature selection [6,10].

**S2.2 Label-blind embedding, rigid assembly, and selection — paragraph 28**

> The canonical Stage 1 pose generator starts from free-nitrene SMILES with explicit hydrogens, unlike the azide input to B5 and CREST. It requests 5,000 ETKDGv3 conformers with seed 20260730 and performs UFF relaxation with a 500-iteration limit per call [11,12,13]. The nitrene nitrogen and its bonded neighbour align the substrate to corresponding reference atoms. Catalyst-core coordinates are copied unchanged and the reference Fe–N distance is checked to 10⁻5 Å. This is rigid catalyst-referenced assembly and screening, not UFF optimisation of the complete catalyst–substrate complex.

**S2.2 Label-blind embedding, rigid assembly, and selection — paragraph 29**

> Candidate acceptance requires zero optimisation status, preserved canonical connectivity, and no severe catalyst–substrate clash. Except for the intended Fe–nitrene-N pair, a separation below 0.65(rₐcov+rbcov) fails the clash screen. The documented covalent radii in Å are H 0.31, B 0.85, C 0.76, N 0.71, O 0.66, F 0.57, Si 1.11, P 1.07, S 1.05, Cl 1.02, Br 1.20, I 1.39, and Fe 1.32. Covalent-radius conventions are described by Cordero and co-workers [14]; the numerical lookup and clash factor above define this study's screen, not a transferable force-field potential. Valid candidates are ordered by UFF score and conformer ID. The lowest 100 and highest 100 non-overlapping valid candidates are retained; fewer than 200 cause failure rather than duplication or padding. An additional cleanup call at writing records final geometry, energy, connectivity, and core checks; pose acceptance reports and run logs are indexed in Section S5.5.

**S2.2 Label-blind embedding, rigid assembly, and selection — paragraph 30**

> No ee or yield is used in generating or selecting poses. Nevertheless, the downstream reaction frame depends on the reported reactive-site atom map. It is therefore a site-conditioned retrospective representation, not evidence of prospective site discovery. Low/high UFF strata are geometric ranks, not free energies, transition states, or Boltzmann populations, and 200 retained poses need not be 200 distinct conformational basins.

**S2.3 Stage 2p fields and compact catalyst information — paragraph 31**

> S2.3 Stage 2p fields and compact catalyst information

**S2.3 Stage 2p fields and compact catalyst information — paragraph 35**

> Zero radial distance receives cosine zero; coincident anchors raise an error. Azimuth is discarded. Catalyst atoms and the anchor nitrene N are excluded from substrate-heavy-atom fields; catalyst context enters via the assembly and screening, whereas C2 contains explicit interaction summaries.

**S2.3 Stage 2p fields and compact catalyst information — paragraph 37**

> Directed all-heavy and heteroatom channels describe mean/90th-percentile axial position and occupancy of 0≤ z≤\| H- N\|, ρ≤2.5 Å. Features are averaged over low-UFF, high-UFF, and combined poses. The 248 columns comprise 198 field means, 36 directed means, four symmetry/antisymmetry summaries, and ten relational features. Relational features compare radial distributions using Wasserstein/energy distances, angular histograms using Jensen–Shannon divergence, and radial means with UFF rank. Standard definitions of the distribution distances are documented in the SciPy reference manual [15,16]. Jensen–Shannon divergence must be distinguished from its square-root distance; the histogram normalisation, logarithm base, and implemented form are specified by the feature source. Exact file-level field ordering still requires the feature manifest.

**S2.4 Occupancy, flexibility, and pose-density visualisations — paragraph 39**

> Stage 2pp produces 655 occupancy/flexibility features using the site-conditioned frame. Its cylindrical grid has 40 axial bins from -8 to 12 Å and 20 radial bins from 0 to 10 Å, at 0.5 Å spacing. Nitrene-centred, carbon-centred, N-to-H, and H-to-N views use all-heavy, carbon, heteroatom, halogen, hydrogen, reactive-carbon, and reactive-hydrogen channels. Atom kernels in (z,ρ) have σₐ=(0.22,0.30rₐvdW) Å and are truncated at three widths. Van der Waals radii in Å are H 1.20, B 1.92, C 1.70, N 1.55, O 1.52, F 1.47, Si 2.10, P 1.80, S 1.80, Cl 1.75, Br 1.85, and I 1.98; other elements use 1.70. Bondi and subsequent main-group tabulations provide the van der Waals radius conventions [17,18]; the listed values, fallback, and kernel-width rule are the explicit computational choices for this representation.

**S2.4 Occupancy, flexibility, and pose-density visualisations — paragraph 40**

> Duplicate-like geometries are balanced within each stratum using a signature of N–H and N–C distances, the N–C–H angle, and the first 40 upper-triangle heavy-atom pair distances. Each component is divided by 0.35 and rounded. This mixed-component quantisation is not a symmetry-aware RMSD cutoff. Signature clusters receive equal weight, shared among their members; combined fields assign half the weight to each UFF stratum. This differs from unweighted Stage 2p means and from Boltzmann weighting.

**S2.4 Occupancy, flexibility, and pose-density visualisations — paragraph 41**

> The archive reports 91 substrate NPZ fields and 91 SVG views, plus paired overlays for 13 shared identities. Each has low-UFF, high-UFF, combined, and difference representations. The release inventory locates these files in the density directories and overlay index described in Section S5.5. The field counts describe the documented geometry inventory; they do not establish distinct conformational basins or mechanistic assignments. Density means geometric occupancy, not electron density or a selectivity-determining interaction.

**S2.4.1 Shared-substrate visualisation: provenance and eligible pairs — paragraph 43**

> The shared-substrate visualisations were constructed from the catalyst-referenced pose data, not from a schematic. The underlying package contains 41 Fe(P7)Cl and 50 Fe(CMC-Por)Cl substrate records, each with 200 retained poses comprising 100 low-UFF and 100 high-UFF poses. The resulting 18,200 catalyst-bound geometries represent sampled configurations of 91 catalyst-domain records, not additional experimental observations. Only the 13 exact canonical substrate identities shared between the datasets were eligible for cross-catalyst overlays; arbitrary P7 and CMC-Por record identifiers were not paired. Figures S2–S4 show the numerical fields, aligned molecular ensembles, and volumetric rendering for the selected identity.

**S2.4.2 Weighted catalyst-frame alignment — paragraph 45**

> Each shared pair was aligned by weighted rigid-body Kabsch fitting [19]. The Fe centre and the four coordinating porphyrin nitrogen atoms were primary anchors, each with weight 8.0. The catalyst-bound substrate nitrene N was a secondary orientation pivot with weight 1.0. This weighting gives priority to catalyst-core superposition while using the substrate pivot to resolve the in-plane orientation. The weights are study-specific alignment choices, not values prescribed by the Kabsch method.

**S2.4.3 Quantitative selection and occupancy comparison — paragraph 51**

> S2.4.3 Quantitative selection and occupancy comparison

**S2.4.3 Quantitative selection and occupancy comparison — paragraph 52**

> The displayed example is shared pair 05: canonical starting-material SMILES Cc1cccc(CCc2ccccc2)c1N=[N+]=[N-], Fe(P7)Cl record 1i, and Fe(CMC-Por)Cl record 2r. For every eligible shared identity, the nitrene__all_heavy__all_200 arrays were normalised to unit total occupancy and compared using Jensen–Shannon divergence, total-variation distance, and Bhattacharyya overlap. Jensen–Shannon divergence and its relationship to variational distance are described by Lin [20]; the Bhattacharyya coefficient measures distributional overlap [21]. For normalised bin masses Pb and Qb, with Mb=(Pb+Qb)/2, the conventions used here are

**S2.4.3 Quantitative selection and occupancy comparison — paragraph 55**

> Pair 05 had the largest JS divergence among the 13 valid shared identities: JS 0.048417 bits, TV 0.161654, and BC 0.961770. The artwork rounds these to 0.0484, 0.1617, and 0.9618, respectively. The complete ranking is recorded in figure2c_shared_pair_ranking.csv. Thus, the displayed pair is the maximum-divergence example within this comparison, not a randomly selected or average shared substrate. Its TV corresponds to redistribution of approximately 16.2% of normalised occupancy mass, not displacement of 16.2% of individual poses. The high BC nevertheless indicates substantial common occupancy.

**S2.4.4 Molecular ensemble rendering — paragraph 57**

> The molecular panels use the aligned 200-model XYZ trajectories, rendered with 3Dmol.js [22]. Each individual catalyst panel shows one frozen catalyst instance and 20 evenly spaced substrate poses from frames 0,10,20,…,190. P7 poses are teal and CMC-Por poses are rust; Fe is dark red and the coordinating nitrogen atoms are blue. An orthographic camera reduces perspective-dependent differences. The shared overlay uses 12 evenly spaced poses from each environment, at frames 0,16,32,…,176, in the same catalyst-core-aligned coordinate frame. The complete 200-frame trajectories remain available in the associated interactive viewer; the printed snapshots display only the stated subsets. Figure S3 presents these individual and shared views.

**S2.4.5 Cylindrical fields and normalised moments — paragraph 59**

> The NPZ arrays contain van-der-Waals-scaled Gaussian atom-occupancy fields with catalyst atoms excluded, using the kernels and weighting described above. Available views are nitrene, activation, N-to-H, and H-to-N; channels are all-heavy, carbon, heteroatom, halogen, hydrogen, reactive carbon, and reactive hydrogen. The stored strata are top 100, bottom 100, all 200, and top-minus-bottom. Figure S2 uses the nitrene/all-heavy/all-200 field, not the signed difference stratum. Its cylindrical grid contains 40 axial bins spanning -8 to 12 Å and 20 radial bins spanning 0 to 10 Å, with 0.5 Å spacing in both dimensions. Figure S2 displays the two fields and their overlay.

**S2.4.5 Cylindrical fields and normalised moments — paragraph 62**

> The cylindrical-field centroids are nearly identical; the difference is principally a reshaping of occupancy rather than a large translation of its centre. These moments describe the normalised sampled fields, not thermodynamic fluctuations.

**S2.4.6 CUBE conversion and interpretation limits — paragraph 66**

> The appropriate interpretation is catalyst-dependent reshaping of accessible spatial occupancy, not complete substrate relocation. The reported comparisons across canonical matches are substrate-dependent: some show visible differences, whereas several have nearly identical all-heavy, all-200 cylindrical fields. The selected example does not establish universally large catalyst-induced geometric changes or a causal explanation of enantioselectivity. These representations are sampled pose occupancies, not transition states, Boltzmann populations, electron densities, free-energy surfaces, or experimentally established selectivity-determining conformations.

**S2.4.6 CUBE conversion and interpretation limits — paragraph 69**

> Figure S2. Cylindrical occupancy fields for the shared canonical substrate. Upper left: Fe(P7)Cl record 1i; upper right: Fe(CMC-Por)Cl record 2r; lower: their overlay. Teal denotes Fe(P7)Cl and orange denotes Fe(CMC-Por)Cl. The all-heavy fields use all 200 retained poses and are plotted against radial distance ρ and axial position z in Å. The normalised-field comparison gives Jensen–Shannon divergence 0.0484 bits, total-variation distance 0.1617, and Bhattacharyya overlap 0.9618.

**S2.4.6 CUBE conversion and interpretation limits — paragraph 72**

> Figure S3. Catalyst-referenced pose ensembles for shared pair 05. Upper left: Fe(P7)Cl record 1i; upper right: Fe(CMC-Por)Cl record 2r. Each individual view displays 20 substrate poses from frames 0,10,…,190 of the aligned 200-model trajectory with one frozen catalyst. Lower: catalyst-core-aligned overlay of 12 poses per environment, from frames 0,16,…,176. Alignment uses Fe and four porphyrin N anchors of weight 8.0 each, with nitrene N of weight 1.0. Teal and rust distinguish P7 and CMC-Por, respectively. These are sampled geometries, not experimentally established reactive conformations.

**S2.4.6 CUBE conversion and interpretation limits — paragraph 74**

> Figure S4. CUBE volumetric view of the shared-substrate occupancy fields for Fe(P7)Cl 1i (teal) and Fe(CMC-Por)Cl 2r (orange), corresponding to the ensembles in Figure S3. The same all-200 cylindrical fields are revolved for visualisation; this is not an independent atom-resolved three-dimensional density calculation. The annotated cylindrical-field metrics show a detectable difference with substantial overlap, consistent with occupancy reshaping rather than complete relocation. The surfaces do not represent electron density, free energy, or Boltzmann populations.

**S3.3 Protocol-matched development results — paragraph 92**

> Table S5. Fe(P7)Cl ee development on the matched 38-substrate cohort. Each block is a separate validation experiment; all rows are Elastic Net results.

**S3.3 Protocol-matched development results — paragraph 94**

> The target- and family-holdout pose gains are 4.029 and 1.072 ee points, or 31.9% and 10.3%, respectively. The occupancy augmentation worsens MAE by 3.851 points (37.5%). Stage 3a-alt changes MAE by only -0.030 points; the combined Stage 3 block lowers MAE by 0.087 but worsens RMSE and R². No paired uncertainty interval for these small Stage 3 changes is available. These comparisons support selective retention of information, not a universal advantage of larger representations. The published descriptor literature provides methodological context, not evidence for these specific gains [6,30].

**S3.4 CREST/GFN2-xTB scope and execution — paragraph 99**

> This comparator uses isolated neutral aryl-azide substrates with explicit hydrogens: no porphyrin, Fe, chloride, catalyst substituent, or frozen-atom constraint is present. Charge 0 and UHF 0 specify the closed-shell calculation. CREST provides automated conformational exploration [5]; the electronic-structure method is GFN2-xTB [31]. The documented logs identify CREST 3.0.2 and xTB 6.7.1, commit edcfbbe.

**S3.4 CREST/GFN2-xTB scope and execution — paragraph 104**

> The calculation record reports 40/40 successful searches, reranks, and JSON single points, with no recorded failures/timeouts. All 40 searches retained one unique minimum, rather than ten. Thus completion is distinct from ensemble diversity, and the result does not prove that each molecule has only one physically accessible conformation. Electronic calls reportedly converged in 11–14 SCF iterations (median 12). Example substrate 1a logs report dielectric constant 4.3300, electronic temperature 300 K, maximum 250 SCF cycles, 10⁻6 Hartree SCF and 10⁻4 e wavefunction convergence; these example settings are not verified for every record.

**S3.5 Population weights and descriptor definitions — paragraph 106**

> S3.5 Population weights and descriptor definitions

**S3.5 Population weights and descriptor definitions — paragraph 109**

> with R=0.00198720425864083 kcal mol⁻1 K⁻1. Reaction temperatures were 60 °C for 20 records, 80 °C for 16, and 100 °C for four, distinct from the logged internal ALPB temperature of 298.15 K. Since each ensemble contains one minimum, p₁=Nₑff=1 and all constant population/energy-variance quantities were excluded from fitting. These are total-energy weights, not calculated free-energy populations.

**S3.5 Population weights and descriptor definitions — paragraph 111**

> The 13 fitted electronic features are total energy per atom, total energy per electron, electronic energy per electron, total-minus-electronic energy per atom, HOMO, LUMO, HOMO–LUMO gap, molecular dipole norm, charge standard deviation, mean absolute charge, charge range, mean atomic-dipole norm, and maximum atomic-dipole norm. HOMO/LUMO use fractional occupations >0.1/≤0.1; orbital energies and the gap are in eV. Element-specific counts and charge extrema for N, O, S, F, Cl, Br, and I form 28 additional audit fields, not fitted features. No catalyst-induced polarisation or catalyst–substrate interaction energy is produced.

**Table 3 in document order — Table S3. Feature definitions retained for interpreting the representation records. Dimensions precede training-fold filtering; the matched development matrices are defined separately in Section S3.**

- Arm | Definition | Columns
- B0 | Training-fold mean | 0
- B1 | Six RDKit descriptors | 6
- B2 | Fifteen RDKit descriptors | 15
- B3 | B2 + 128-bit Morgan | 143
- B4 | B2 + 256-bit Morgan | 271
- B5 | B2 + 1,024-bit Morgan | 1,039
- P0 | Stage 2p catalyst-referenced fields | 248
- P1 | B1 + P0 | 254
- P2 | B5 + all P0 features | 1,287
- P3 | B5 + compact C1 geometry | 1,083
- P4 | B5 + C1 + C2 catalyst interactions | 1,099

**Table 4 in document order — The normalised-field moments for the selected identity are:**

- tabular{@{}lrr@{}} Quantity | Fe(P7)Cl 1i | Fe(CMC-Por)Cl 2r
- Mean axial z (Å) | 4.381 | 4.418
- Mean radial ρ (Å) | 2.112 | 2.178
- Axial standard deviation (Å) | 2.374 | 2.516
- Radial standard deviation (Å) | 1.088 | 1.069
- z–ρ covariance (Å²) | 0.474 | 0.255
- tabular |  | 

**Table 6 in document order — Table S5. Fe(P7)Cl ee development on the matched 38-substrate cohort. Each block is a separate validation experiment; all rows are Elastic Net results.**

- Protocol and representation | MAE | RMSE | R²
- Target holdout: structure only | 12.612 | 15.183 | 0.064
- Target holdout: structure + pose | 8.583 | 11.932 | 0.422
- Family holdout: structure only | 10.406 | 13.525 | 0.257
- Family holdout: structure + pose | 9.334 | 12.557 | 0.359
- Occupancy comparison: local geometry | 10.281 | 13.023 | 0.311
- Occupancy comparison: +655 features | 14.132 | 17.005 | -0.175
- Nested families: locked geometry | 8.498 | 11.357 | 0.476
- Nested families: +Stage 3a-alt | 8.468 | 11.289 | 0.482
- Nested families: +Stage 3b | 8.664 | 11.978 | 0.417
- Nested families: +Stage 3a-alt +Stage 3b | 8.411 | 11.810 | 0.433

**Table 7 in document order — Table S6. Nested-family CREST ablations, same 38 Fe(P7)Cl substrates. Dimensions are before fold-local filtering.**

- Representation | Columns | MAE | RMSE | R²
- Locked geometry | 248 | 8.498 | 11.357 | 0.476
- +CREST geometry | 258 | 8.858 | 11.578 | 0.455
- +xTB electronic | 261 | 8.610 | 11.745 | 0.440
- +Both blocks | 271 | 8.876 | 11.860 | 0.429
