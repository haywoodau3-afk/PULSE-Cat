# PPTL computational report

Status: generated from persisted artifacts

## Interpretation lock for manuscript use

The guarded ensemble improves the matched retrospective EE error in both
directions, but it does not meet the prespecified 10% progressive-AUC
superiority gate. Pose arms therefore remain conditional secondary evidence:
they provide directional early-label diagnostics and domain-shift explanations,
not a universal claim that pose features outperform the 2D B5 baseline. The
report contains no prospective experimental outcomes.

## Bidirectional aryl replay

- Planned paired pose panel: 13
- Canonical pairs in current ledger: 13
- Canonical aryl pairs: 13

| Direction | Target-only MAE | Guarded MAE | Excluded overlaps |
| --- | ---: | ---: | ---: |
| cmcpor_to_p7_aryl | 11.815349181945432 | 11.65378368398854 | 13 |
| p7_to_cmcpor_aryl | 12.233930728492268 | 11.701571019876303 | 13 |

## Feature-arm matrix

| Arm | Direction | Target-only MAE | Guarded MAE | n |
| --- | --- | ---: | ---: | ---: |
| B5 | cmcpor_to_p7_aryl | 11.815349181945432 | 11.65378368398854 | 37 |
| B5 | p7_to_cmcpor_aryl | 12.233930728492268 | 11.701571019876303 | 31 |
| P3 | cmcpor_to_p7_aryl | 11.27581943294034 | 10.973149884711114 | 37 |
| P3 | p7_to_cmcpor_aryl | 12.205326517111706 | 11.4802564031599 | 31 |
| P4 | cmcpor_to_p7_aryl | 11.06116958300058 | 10.741301225713725 | 37 |
| P4 | p7_to_cmcpor_aryl | 12.208276490408817 | 11.509373356611247 | 31 |

## Yield feature-arm matrix

| Arm | Direction | Target-only MAE | Guarded MAE | n |
| --- | --- | ---: | ---: | ---: |
| B5 | cmcpor_to_p7_aryl | 13.76160667859282 | 13.537115017326334 | 38 |
| B5 | p7_to_cmcpor_aryl | 16.19384316888603 | 15.675358486474465 | 31 |
| P3 | cmcpor_to_p7_aryl | 15.377192965588964 | 14.902743137241645 | 38 |
| P3 | p7_to_cmcpor_aryl | 17.367181297348008 | 16.463506856117395 | 31 |
| P4 | cmcpor_to_p7_aryl | 15.215952099745147 | 14.503344437597883 | 38 |
| P4 | p7_to_cmcpor_aryl | 18.47318981026089 | 17.108689910466886 | 31 |

## Scaffold-held-out replay

| Direction | Scaffold groups | Predictions | Target-only MAE | Combined MAE | Guarded MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| fe-p7-cl → cmcpor-fecl | 12 | 636 | 24.10284000231864 | 18.22257665361862 | 18.381569109822223 |
| cmcpor-fecl → fe-p7-cl | 22 | 1202 | 14.81606692682318 | 13.267495781099672 | 10.64288261882593 |
| fe-p7-cl → cmcpor-fecl | 12 | 636 | 20.967782170997 | 19.028284353522526 | 18.073481657964468 |
| cmcpor-fecl → fe-p7-cl | 22 | 1202 | 14.540500154126201 | 12.980810985541197 | 11.289369764542858 |
| fe-p7-cl → cmcpor-fecl | 12 | 636 | 22.236119421641632 | 19.40190303484444 | 18.5306162320642 |
| cmcpor-fecl → fe-p7-cl | 22 | 1202 | 14.239808734968427 | 11.919575756552208 | 10.214801003235122 |

## Scaffold-bootstrap intervals

| Direction | Delta | Mean | 2.5% | 97.5% |
| --- | --- | ---: | ---: | ---: |
| fe-p7-cl → cmcpor-fecl | active_source_minus_target | 1.3756023705024614 | -3.38836629923051 | 6.273734252021524 |
| fe-p7-cl → cmcpor-fecl | combined_minus_target | -1.5026836880570218 | -4.9275361943281455 | 1.8783439148152985 |
| fe-p7-cl → cmcpor-fecl | guarded_minus_target | -2.2078385924224313 | -4.567307299529356 | -0.6440454571956518 |
| cmcpor-fecl → fe-p7-cl | active_source_minus_target | 1.1693737096593546 | -6.414820964914016 | 7.517219513925314 |
| cmcpor-fecl → fe-p7-cl | combined_minus_target | -2.874566689621849 | -6.698321861783581 | 0.43326439335370787 |
| cmcpor-fecl → fe-p7-cl | guarded_minus_target | -4.595600429776116 | -7.848172770140257 | -1.8879321353975476 |

## Random-route replicate summaries

| Target | Arm | Direction | Routes | Mean MAE | Mean guarded AUC | Mean target AUC |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| ee_percent | B5 | cmcpor_to_p7_aryl | 500 | 12.416921721793681 | 446.0544418277559 | 453.55959961096016 |
| ee_percent | B5 | p7_to_cmcpor_aryl | 500 | 12.91078079484714 | 386.410829591859 | 397.7591894317412 |
| ee_percent | P3 | cmcpor_to_p7_aryl | 500 | 12.075496274399683 | 432.87074232807436 | 442.6724981707911 |
| ee_percent | P3 | p7_to_cmcpor_aryl | 500 | 12.564517782034937 | 373.06035034544186 | 385.3272955121284 |
| ee_percent | P4 | cmcpor_to_p7_aryl | 500 | 11.927876969335479 | 426.8748588818182 | 440.7248135263251 |
| ee_percent | P4 | p7_to_cmcpor_aryl | 500 | 12.813211878622523 | 380.4282576613773 | 393.895945933615 |

## Random-route bootstrap intervals

| Target | Arm | Direction | Delta | Mean | 2.5% | 97.5% |
| --- | --- | --- | --- | ---: | ---: | ---: |
| ee_percent | B5 | cmcpor_to_p7_aryl | mae_delta_guarded_minus_target | -0.2298944126239528 | -0.25359514876509026 | -0.20514370891759046 |
| ee_percent | B5 | cmcpor_to_p7_aryl | auc_delta_guarded_minus_target | -7.504835936592151 | -8.331366928493575 | -6.632907723787113 |
| ee_percent | B5 | p7_to_cmcpor_aryl | mae_delta_guarded_minus_target | -0.3992536332575958 | -0.44299580519295323 | -0.35611750344426696 |
| ee_percent | B5 | p7_to_cmcpor_aryl | auc_delta_guarded_minus_target | -11.344081516759605 | -12.626693286579895 | -10.08912604403007 |
| ee_percent | P3 | cmcpor_to_p7_aryl | mae_delta_guarded_minus_target | -0.31109523033687025 | -0.3451109612724135 | -0.2791479196029475 |
| ee_percent | P3 | cmcpor_to_p7_aryl | auc_delta_guarded_minus_target | -9.802708933226086 | -11.0067968330454 | -8.69069737347735 |
| ee_percent | P3 | p7_to_cmcpor_aryl | mae_delta_guarded_minus_target | -0.460024761897187 | -0.49887284254704845 | -0.42147752903520125 |
| ee_percent | P3 | p7_to_cmcpor_aryl | auc_delta_guarded_minus_target | -12.26638247928319 | -13.398542706977594 | -11.20731516046058 |
| ee_percent | P4 | cmcpor_to_p7_aryl | mae_delta_guarded_minus_target | -0.4165647965013515 | -0.4514498997631134 | -0.38216429031943105 |
| ee_percent | P4 | cmcpor_to_p7_aryl | auc_delta_guarded_minus_target | -13.837656557736835 | -15.05738694354609 | -12.670929776997882 |
| ee_percent | P4 | p7_to_cmcpor_aryl | mae_delta_guarded_minus_target | -0.500572203890209 | -0.5334710554426203 | -0.465749823546462 |
| ee_percent | P4 | p7_to_cmcpor_aryl | auc_delta_guarded_minus_target | -13.453391870016786 | -14.365914402201174 | -12.504963160488968 |

## Matched-route incremental pose bootstrap

| Pose arm | Direction | MAE delta vs B5 | AUC delta vs B5 |
| --- | --- | ---: | ---: |
| P3 | cmcpor_to_p7_aryl | -0.341726239533276 [-0.3999608082210321, -0.28243771067891354] | -13.19130002904902 [-15.093949790029937, -11.302977469340757] |
| P3 | p7_to_cmcpor_aryl | -0.34706023402402847 [-0.41463513348070863, -0.27959694686185804] | -13.373342656993216 [-15.190699829500026, -11.682339696817282] |
| P4 | cmcpor_to_p7_aryl | -0.4894278403315963 [-0.5499999839284515, -0.43196976855072583] | -19.18282081926479 [-21.14680210724761, -17.22503072669576] |
| P4 | p7_to_cmcpor_aryl | -0.09890917937994667 [-0.17651568753557764, -0.02043921090114368] | -6.013529946045317 [-8.034594768191107, -3.9330142458744652] |

## Pose controls

| Direction | Arm | Target-only MAE | Combined MAE | Guarded MAE |
| --- | --- | ---: | ---: | ---: |
| cmcpor_to_p7_aryl | B5 | 11.815349181945432 | 11.229532023775223 | 11.653783683988538 |
| cmcpor_to_p7_aryl | P2 | 16.953282274482657 | 11.627744314959617 | 14.456915513723427 |
| cmcpor_to_p7_aryl | P2_permuted | 14.253716255240954 | 13.07819128935193 | 13.792798188604174 |
| cmcpor_to_p7_aryl | P2_random | 11.673777497220366 | 14.155379791508352 | 12.161660093527116 |
| cmcpor_to_p7_aryl | P3 | 11.27581943294034 | 10.7766884443175 | 10.973149884711113 |
| cmcpor_to_p7_aryl | P3_permuted | 12.05037980766687 | 11.69034479852338 | 11.623015489637622 |
| cmcpor_to_p7_aryl | P3_random | 11.681951487894702 | 12.771790961289918 | 11.890553111623126 |
| p7_to_cmcpor_aryl | B5 | 12.233930728492268 | 12.817051629305277 | 11.701571019876305 |
| p7_to_cmcpor_aryl | P2 | 17.659464679323474 | 14.66765940839428 | 14.239076986007982 |
| p7_to_cmcpor_aryl | P2_permuted | 18.75230747848889 | 16.680329257768754 | 17.289147845657528 |
| p7_to_cmcpor_aryl | P2_random | 15.028329956841782 | 13.362215651976866 | 14.46789358537254 |
| p7_to_cmcpor_aryl | P3 | 12.205326517111706 | 13.167907628939515 | 11.480256403159903 |
| p7_to_cmcpor_aryl | P3_permuted | 12.855473310206547 | 13.28179200646515 | 12.373300478584389 |
| p7_to_cmcpor_aryl | P3_random | 14.030438099360664 | 13.07588061354896 | 13.356516862957601 |

## Compact pose residual upgrade

- Pose arm: P3_compact_stage2p; compact feature count: 44

| Direction | B5 target MAE | Residual-pose target MAE | Direct compact-pose pooled MAE | Guarded residual-pose MAE |
| --- | ---: | ---: | ---: | ---: |
| cmcpor_to_p7_aryl | 11.815349181945432 | 12.322670927924857 | 11.471740857456762 | 12.24416445709421 |
| p7_to_cmcpor_aryl | 12.233930728492268 | 12.021027191923471 | 13.762306408204905 | 11.411784601877809 |

Pose is evaluated as a cross-fitted residual correction and as a compact direct augmentation. The raw 248-column concatenation remains a diagnostic control.

## Yield compact pose residual upgrade

| Direction | B5 target MAE | Residual-pose target MAE | Guarded residual-pose MAE |
| --- | ---: | ---: | ---: |
| cmcpor_to_p7_aryl | 13.76160667859282 | 15.397988293814569 | 13.85878921234828 |
| p7_to_cmcpor_aryl | 16.19384316888603 | 17.462184248103615 | 16.916394017972255 |

## Scaffold incremental pose bootstrap

| Pose arm | Direction | Target MAE delta vs B5 | Guarded MAE delta vs B5 |
| --- | --- | ---: | ---: |
| P3 | fe-p7-cl → cmcpor-fecl | -2.1709293981354074 [-4.603374165777031, -0.012389978610583927] | -1.8262629760420754 [-3.9682760036517544, 0.2721594565582383] |
| P3 | cmcpor-fecl → fe-p7-cl | -0.13262693878870624 [-1.837496312450556, 1.4558310746459693] | 0.6656576762301213 [-0.5891281097067301, 1.8562191907015502] |
| P4 | fe-p7-cl → cmcpor-fecl | -0.914087653644704 [-2.8996198426078412, 0.8480771683862498] | -1.8040073669131906 [-5.290278694434815, 1.5431174397236582] |
| P4 | cmcpor-fecl → fe-p7-cl | -0.7779941957364601 [-2.9876014959697867, 1.1288186114120313] | -0.9423374508108838 [-3.309887317757121, 1.0359006833890487] |

## Resource ledger

| Domain | Arm | Features | Feature seconds | Peak RSS (bytes) |
| --- | --- | ---: | ---: | ---: |
| cmcpor_aryl | B1 | 6 | 0.01662916608620435 | 459112448 |
| cmcpor_aryl | B5 | 1039 | 0.01657366589643061 | 459112448 |
| cmcpor_aryl | P0 | 248 | 0.016422624932602048 | 459112448 |
| cmcpor_aryl | P2 | 1287 | 0.016534124966710806 | 459112448 |
| cmcpor_aryl | P3 | 1083 | 0.01651333295740187 | 459112448 |
| cmcpor_aryl | P4 | 1099 | 0.016505916020832956 | 459112448 |
| p7 | B1 | 6 | 0.020809917012229562 | 459112448 |
| p7 | B5 | 1039 | 0.020304000005126 | 459112448 |
| p7 | P0 | 248 | 0.020312707987613976 | 459112448 |
| p7 | P2 | 1287 | 0.020070667029358447 | 459112448 |
| p7 | P3 | 1083 | 0.02017633302602917 | 459112448 |
| p7 | P4 | 1099 | 0.020177874946966767 | 459112448 |

## Evidence boundary

This report represents a computational, label-masked replay. It is not prospective wet-lab validation and does not establish a GNN head-to-head result.
