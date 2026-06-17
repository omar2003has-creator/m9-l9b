
from linker.candidates import candidates
from linker.disambiguate import disambiguate
from linker.types import LinkResult
def link(
    driver,
    doc_id: str,
    text: str,
    ner_spans: list[tuple[int, int, str, str]],
) -> list[LinkResult]:
    results = []
    doc_resolved = []

    for start, end, surface, ner_label in ner_spans:
        cands = candidates(driver, surface)

        if not cands:
            chosen, reason = None, "nil-no-candidates"
        elif len(cands) == 1:
            chosen, reason = cands[0], "resolved-unique"
        else:
            chosen, reason = disambiguate(driver, cands, ner_label, doc_resolved)

        lr = LinkResult(
            doc_id=doc_id,
            start=start,
            end=end,
            surface=surface,
            predicted_node_id=chosen["id"] if chosen else None,
            predicted_type_label=chosen["labels"][0] if chosen else None,
            reason=reason,
        )
        results.append(lr)
        doc_resolved.append(lr)

    return results