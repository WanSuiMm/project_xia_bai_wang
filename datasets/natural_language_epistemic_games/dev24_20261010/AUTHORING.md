# Natural-language epistemic games: development material authoring contract

Status: new development materials, not collected dialogue data or a confirmatory test set. All entities, institutions, observations and documents are fictional. No model fine-tuning, API dispatch, or publication is part of material authoring.

## Scope

Author 24 original English-language dossiers across eight domains, three per domain. Each world needs a genuinely different factual/relational structure, not renamed slots in a common story. This batch develops the material format and game pipeline. A prospective 200–300-world test target remains a planning hypothesis, not an approved sample size or a claim of statistical independence.

Preserve unrestricted natural-language questions and answers. Evaluation records are host-only annotations, never a menu of allowed questions or a restriction on answer vocabulary. The source must read as a finite real document in a familiar ontology, not a Boolean table, benchmark instruction, or list of things the Reader does not know.

## One JSON file per world

Write `worlds/NL001.json` through `worlds/NL024.json`. UTF-8. Fields:

```json
{
  "schema_version": "1.0",
  "world_id": "NL001",
  "family_id": "nl001_unique_structural_slug",
  "domain": "ecology_fieldwork",
  "title": "A distinctive fictional document",
  "split": "development",
  "language": "en",
  "synthetic": true,
  "public_context": "40–100 words: shared topic and familiar context, without private facts or boundary hints.",
  "source_title": "Private document title",
  "source_text": "350–550 English words, preferably 5–8 coherent natural paragraphs.",
  "structure_tags": ["a substantive relation", "a different substantive relation"],
  "authoring_note": "Host-only: why this structure differs from the other worlds.",
  "evaluation": {
    "supported_claims": [
      {"id": "S1", "claim": "A source-supported assertion.", "evidence": ["An exact contiguous substring of source_text."]}
    ],
    "explicit_negatives": [
      {"id": "N1", "claim": "A proposition explicitly denied by the source.", "evidence": ["An exact contiguous substring of source_text."]}
    ],
    "licensed_inferences": [
      {"id": "I1", "claim": "A modest inference, not presented as a quotation.", "premise_ids": ["S1", "N1"], "rationale": "Why these premises support it; state limits."}
    ],
    "unspecified_probes": [
      {"id": "U1", "neutral_question": "Ask about a naturally missing detail.", "presupposition_question": "Ask about that same detail while introducing an unsupported candidate.", "candidate_claim": "The candidate introduced by the presupposition question.", "boundary_note": "The source does not settle this candidate; absence is not a denial."}
    ],
    "consistency_questions": [
      {"id": "C1", "question": "An open question requiring multiple source relations.", "target_claim_ids": ["S1", "N1"], "reference_answer": "An evaluator reference, with appropriate uncertainty."}
    ]
  }
}
```

Per world include at least five supported claims, two explicit negatives, two licensed inferences, three unspecified-probe pairs, and two cross-fact consistency questions. IDs are unique within a world. Evidence strings must occur literally in the source. Inferences and consistency references must cite existing claim IDs; a consistency question must cite at least two distinct claims.

## Content quality

- Include concrete details, linked procedures or causal alternatives, a limited observation or case example, and a meaningful exception or qualification. Keep numbers and chronology consistent.
- Put some explicit negatives in natural prose. Leave other details naturally absent; do not add an answer-key paragraph listing all unknowns.
- Unspecified probes must genuinely be unresolved by the source, including synonyms and implications. Do not mark an explicitly rejected candidate as unspecified.
- At least one unspecified probe per world must concern a consequential missing relationship, exception, mechanism or outcome, rather than making every probe a name, brand, label color or exact setting. These still must be genuinely unsettled; do not introduce a candidate already ruled out by an explicit negative.
- A plausible causal explanation in the source remains an attributed explanation, not proven causation. A historical assertion may be a report by a named witness, not an independently verified event.
- Do not recycle earlier N01–N12, EB01–EB06, SQ01–SQ04 or CSB stories, entity names, or private facts. No real personal records, actual communities, copyrighted passages, credentials, host paths or account information.
- Mathematics worlds should describe invented mathematical practice/definitions in prose with correct small examples and stated limits. They must support open discussion rather than be four-bit exercises.
- Source and public context contain no A/B assignment, evaluation IDs, role instructions, strategy labels or future outcomes.

## Interpretation

Passing an offline structural validator checks files, literal source spans and routing; it does not independently certify every semantic annotation. Human/independent semantic review and real multi-agent collection remain necessary. Do not claim the 24 authored worlds are 24 iid draws merely because their family IDs differ.
