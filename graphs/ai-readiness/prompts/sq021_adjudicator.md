Document: "{title}". Section: {section_path}.

An extraction instrument proposed this item for a knowledge graph of the document, typed "{claim_kind}":

ITEM: {item}

and located this span for it, cut verbatim from the chunk below:

SPAN: "{span}"

A second instrument rated the proposal against a fixed rubric and disagreed with it:
- claim_made: {rater_claim_made}
- span_is_evidence: {rater_span_is_evidence}
- rationale: {rater_rationale}

You are the adjudicator. Decide the two questions yourself, on the chunk's text alone:
1. claim_made: Does the chunk itself assert this item as typed? For a node: the text presents it as that kind of thing (a concept the text uses, a definition the text gives, a claim the text makes, an instrument, measure, standard, framework, practice, tool or platform the text describes), and every property value shown is read from the text, not invented or completed from background knowledge. For an edge: the text states this relationship between the two endpoints. Answer no for boilerplate, navigation, a misreading, or an item the text does not support.
2. span_is_evidence: Is the span the evidence for the item, that is, does this text itself state or name it?

Answer with exactly this JSON and nothing else:
{"claim_made": true, "span_is_evidence": true, "rationale": "one sentence naming what decided it"}

CHUNK:
"""
{segment_text}
"""
