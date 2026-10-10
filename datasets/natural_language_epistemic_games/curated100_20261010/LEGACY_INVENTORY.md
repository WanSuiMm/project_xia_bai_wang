# Legacy natural-language world inventory

**Inventory date:** 2026-10-10  
**Status:** offline source inventory; every included row is marked `exploratory_only`.

The inventory contains **30 candidate source-world families** and 42 complete English source strings (including retained variants). It copies full source text into the JSON so the parent dataset can reuse material without reopening trajectory records.

## Counts and scope

| Legacy source set | Candidate worlds |
|---|---:|
| Naturalistic Study 1 cards | 12 |
| Strategic bluff cards | 2 |
| Epistemic Boundary Mimicry | 6 |
| Strategic qualification | 4 |
| Counterfactual source-boundary families | 6 |
| **Total** | **30** |

Count one source-world/case family. Naturalistic and strategic cards remain one world when reused across role instructions, retries or trajectories. Each EB01–EB06 family has one shared public context; its second full source is retained as an in-family variant. Each CS01–CS06 `source_v1` is retained as a full counterfactual version of its `source_v0`, so neither adds a world. Strong, boundary-aware and frozen arms, seat variants, model/provider runs and replay trajectories do not add worlds.

The explicitly excluded material is the early Boolean tables, JES32 and OSI48 pure probability-question material. All 30 included families have a complete English source; there are no missing-source exclusions in this inventory.

## Candidate families

`source_text` and every full-text variant are in `LEGACY_INVENTORY.json`; references below use paths relative to the `project_xia_bai_wang` repository root.

| Legacy ID | Original ID | Domain | Topic | Title | Canonical source reference | Variants |
|---|---|---|---|---|---|---:|
| LEGACY_N01 | N01 | history_institutions | evening berth, inspection admission, and port queue order | The Veyran Evening Berth Accord | `naturalistic_study_1/cards/N01.json#source_text` | 0 |
| LEGACY_N02 | N02 | history_institutions | guild repair seals, independent inspection, and liability | The Kelvor Guild's Joint Seal | `naturalistic_study_1/cards/N02.json#source_text` | 0 |
| LEGACY_N03 | N03 | history_institutions | archaeological storage slips and the interpretation of a sealed deposit | The Ash-Step Archive at Morven Reach | `naturalistic_study_1/cards/N03.json#source_text` | 0 |
| LEGACY_N04 | N04 | anthropology_social | neighborhood custom around the ferry's after-dark timetable | The Lantern Passage at Mallow Quay | `naturalistic_study_1/cards/N04.json#source_text` | 0 |
| LEGACY_N05 | N05 | anthropology_social | orchard plot-use claims and successor eligibility | Use Claims at Fenlock Hill Orchard | `naturalistic_study_1/cards/N05.json#source_text` | 0 |
| LEGACY_N06 | N06 | anthropology_social | cooperative press access, harvest shifts, and seasonal maintenance | Harvest Work at the Gable Press Cooperative | `naturalistic_study_1/cards/N06.json#source_text` | 0 |
| LEGACY_N07 | N07 | science_nature | leaf-posture response to flooding and root-zone aeration | The rain-lift response of lantern fenleaf | `naturalistic_study_1/cards/N07.json#source_text` | 0 |
| LEGACY_N08 | N08 | science_nature | larval case orientation under stream-current conditions | Current-following cases of the shale ribbon larva | `naturalistic_study_1/cards/N08.json#source_text` | 0 |
| LEGACY_N09 | N09 | science_nature | humidity bands and acoustic-tile behavior | Humidity bands in reedlace acoustic tile | `naturalistic_study_1/cards/N09.json#source_text` | 0 |
| LEGACY_N10 | N10 | math_language | Vale Strip Balance: mathematical and linguistic procedure | Vale Strip Balance | `naturalistic_study_1/cards/N10.json#source_text` | 0 |
| LEGACY_N11 | N11 | math_language | Rovelin final-stop patterns | Final Stops in Rovelin | `naturalistic_study_1/cards/N11.json#source_text` | 0 |
| LEGACY_N12 | N12 | math_language | Keldan petition folio and its language rules | Keldan Petition Folio | `naturalistic_study_1/cards/N12.json#source_text` | 0 |
| LEGACY_S01 | S01 | social_institution | community seed-room register, collection limits, and failed-crop eligibility | Orren Seed Room: autumn register extract | `strategic_bluff_pilot/cards/S01.json#source_text` | 0 |
| LEGACY_S02 | S02 | science_nature | dapplefin contrast observations at a fictional field station | Dapplefin contrast notes from the Vale Mere station | `strategic_bluff_pilot/cards/S02.json#source_text` | 0 |
| LEGACY_EB01 | EB01 | materials_science | laminated panel shape changes after damp/dry room transfers | Foldglass panels across damp and dry rooms | `epistemic_boundary_mimicry/materials/frozen_pack_20261004/cards.json#[case_id=EB01].sources[0].source_text` | 1 |
| LEGACY_EB02 | EB02 | civic_institutions | temporary boarding priority and records during ferry interruption | Storm boarding slips at Mallow Ford | `epistemic_boundary_mimicry/materials/frozen_pack_20261004/cards.json#[case_id=EB02].sources[0].source_text` | 1 |
| LEGACY_EB03 | EB03 | ecology | moth resting position after shade-screen rearrangement | Silverfold moth resting positions at Nacre Ridge | `epistemic_boundary_mimicry/published_runs/go_frozen_pair_completed_20261004/bundle.json#EB03_D1_symmetric_frozen.sources[0].source_text` | 1 |
| LEGACY_EB04 | EB04 | archaeology_conservation | conservation observations for painted clay inventory tags | Painted clay inventory-tag conservation | `epistemic_boundary_mimicry/published_runs/go_frozen_pair_completed_20261004/bundle.json#EB04_D1_symmetric_frozen.sources[0].source_text` | 1 |
| LEGACY_EB05 | EB05 | civic_institutions | temporary access tokens during a hillside footbridge closure | Access tokens during footbridge repairs | `epistemic_boundary_mimicry/published_runs/go_surface_diverse_cutoff_20261005/bundle.json#cases[case_id=EB05].sources[0].source_text` | 1 |
| LEGACY_EB06 | EB06 | ecology | seed wrapping and emergence of an invented marsh plant | Paper wrapping and marsh-plant emergence | `epistemic_boundary_mimicry/published_runs/go_surface_diverse_cutoff_20261005/bundle.json#cases[case_id=EB06].sources[0].source_text` | 1 |
| LEGACY_SQ01 | SQ01 | archival administration | returned ledgers at the tavren borough archive | Returned Ledgers at the Tavren Borough Archive | `epistemic_boundary_mimicry/strategic_qualification/materials_20261008.json#cases[case_id=SQ01].source_text` | 0 |
| LEGACY_SQ02 | SQ02 | ecology | evening counts in the selnor basin | Evening Counts in the Selnor Basin | `epistemic_boundary_mimicry/strategic_qualification/materials_20261008.json#cases[case_id=SQ02].source_text` | 0 |
| LEGACY_SQ03 | SQ03 | material preservation | a dry-pad cleaning trial for bronze register weights | A Dry-Pad Cleaning Trial for Bronze Register Weights | `epistemic_boundary_mimicry/strategic_qualification/materials_20261008.json#cases[case_id=SQ03].source_text` | 0 |
| LEGACY_SQ04 | SQ04 | linguistic fieldwork | elicitation notebook from the orvani ridge | Elicitation Notebook from the Orvani Ridge | `epistemic_boundary_mimicry/strategic_qualification/materials_20261008.json#cases[case_id=SQ04].source_text` | 0 |
| LEGACY_CS01 | CS01 | institutional history: canal waterworks | maintenance rights at peldrin canal's sedge reach | Maintenance Rights at Peldrin Canal's Sedge Reach | `epistemic_boundary_mimicry/counterfactual_source_boundary/materials_20261008.json#[case_id=CS01].source_v0` | 1 |
| LEGACY_CS02 | CS02 | institutional history: ferry cooperative | night ferry rules of the edrin sound trust | Night Ferry Rules of the Edrin Sound Trust | `epistemic_boundary_mimicry/counterfactual_source_boundary/materials_20261008.json#[case_id=CS02].source_v0` | 1 |
| LEGACY_CS03 | CS03 | ecology: coastal dune succession | seed drift along the esh hollow dune line | Seed Drift Along the Esh Hollow Dune Line | `epistemic_boundary_mimicry/counterfactual_source_boundary/materials_20261008.json#[case_id=CS03].source_v0` | 1 |
| LEGACY_CS04 | CS04 | materials science: porous ceramic composites | freeze cycling of tuff-and-ash hearth tiles | Freeze Cycling of Tuff-and-Ash Hearth Tiles | `epistemic_boundary_mimicry/counterfactual_source_boundary/materials_20261008.json#[case_id=CS04].source_v0` | 1 |
| LEGACY_CS05 | CS05 | linguistics: coastal weather lexicon | wind words at the varo sound inlet | Wind Words at the Varo Sound Inlet | `epistemic_boundary_mimicry/counterfactual_source_boundary/materials_20261008.json#[case_id=CS05].source_v0` | 1 |
| LEGACY_CS06 | CS06 | mathematics: river geomorphology | arc fits for the thawing kestrel bend | Arc Fits for the Thawing Kestrel Bend | `epistemic_boundary_mimicry/counterfactual_source_boundary/materials_20261008.json#[case_id=CS06].source_v0` | 1 |

## Deduplication and interpretation

The source-level grouping follows the original case/public-context families. Exact normalized-text comparison found no duplicate canonical source texts among the 30 rows, no duplicate text among all 42 retained source strings, and no exact text match against dev24_20261010 NL001–NL024. This is a literal-text check; it does not establish semantic independence. Several materials share broad domains such as civic records, ecology, conservation, materials, linguistics or mathematics, so review factual skeletons before selecting the final 100.

These are hand-authored or exploratory materials from heterogeneous projects, not a probability sample. **A common distribution, representativeness, exchangeability and statistical independence are not guaranteed.**

See `LEGACY_INVENTORY.json` for full source text, variants, per-family notes, machine-readable references and explicit exclusions.

