# PPTL computational report

Status: generated from persisted artifacts

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
| B1 | cmcpor_to_p7_aryl | 12.894696118257428 | 12.802350329142925 | 37 |
| B1 | p7_to_cmcpor_aryl | 14.24301827649014 | 13.052987704037347 | 31 |
| B2 | cmcpor_to_p7_aryl | 12.714387603724369 | 12.529223994607138 | 37 |
| B2 | p7_to_cmcpor_aryl | 14.099973511797844 | 12.955489600386166 | 31 |
| B3 | cmcpor_to_p7_aryl | 11.941464348016797 | 11.612239505541964 | 37 |
| B3 | p7_to_cmcpor_aryl | 12.562631860710194 | 12.082518369494581 | 31 |
| B4 | cmcpor_to_p7_aryl | 12.165392036521489 | 11.963982907354863 | 37 |
| B4 | p7_to_cmcpor_aryl | 12.577848567216213 | 11.780500826399702 | 31 |
| B5 | cmcpor_to_p7_aryl | 11.815349181945432 | 11.65378368398854 | 37 |
| B5 | p7_to_cmcpor_aryl | 12.233930728492268 | 11.701571019876303 | 31 |

## Scaffold-held-out replay

| Direction | Scaffold groups | Predictions | Target-only MAE | Combined MAE | Guarded MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| fe-p7-cl → cmcpor-fecl | 12 | 636 | 24.10284000231864 | 18.22257665361862 | 18.381569109822223 |
| cmcpor-fecl → fe-p7-cl | 22 | 1202 | 14.81606692682318 | 13.267495781099672 | 10.64288261882593 |

## Scaffold-bootstrap intervals

| Direction | Delta | Mean | 2.5% | 97.5% |
| --- | --- | ---: | ---: | ---: |
| fe-p7-cl → cmcpor-fecl | active_source_minus_target | 1.3756023705024614 | -3.38836629923051 | 6.273734252021524 |
| fe-p7-cl → cmcpor-fecl | combined_minus_target | -1.5026836880570218 | -4.9275361943281455 | 1.8783439148152985 |
| fe-p7-cl → cmcpor-fecl | guarded_minus_target | -2.2078385924224313 | -4.567307299529356 | -0.6440454571956518 |
| cmcpor-fecl → fe-p7-cl | active_source_minus_target | 1.1693737096593546 | -6.414820964914016 | 7.517219513925314 |
| cmcpor-fecl → fe-p7-cl | combined_minus_target | -2.874566689621849 | -6.698321861783581 | 0.43326439335370787 |
| cmcpor-fecl → fe-p7-cl | guarded_minus_target | -4.595600429776116 | -7.848172770140257 | -1.8879321353975476 |

## Evidence boundary

This report represents a computational, label-masked replay. It is not prospective wet-lab validation and does not establish a GNN head-to-head result.
