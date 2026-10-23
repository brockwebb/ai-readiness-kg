Document: "{title}". Section: {section_path}.

An extraction instrument read the chunk below and proposed this item for a knowledge graph of the document, typed "{claim_kind}":

ITEM: {item}

and located this span for it, cut verbatim from the chunk:

SPAN: "{span}"

Rubric (fixed before any rating was made). Answer two questions, each yes or no:
1. claim_made: Does the chunk itself assert this item as typed? For a node: the text presents it as that kind of thing (a concept the text uses, a definition the text gives, a claim the text makes, an instrument, measure, standard, framework, practice, tool or platform the text describes), and every property value shown is read from the text, not invented or completed from background knowledge. For an edge: the text states this relationship between the two endpoints. Answer no for boilerplate, navigation, a misreading, or an item the text does not support.
2. span_is_evidence: Is the span the evidence for the item, that is, does this text itself state or name it?

Answer with exactly this JSON and nothing else:
{"claim_made": true, "span_is_evidence": true, "rationale": "one sentence"}

CHUNK:
"""
{segment_text}
"""
