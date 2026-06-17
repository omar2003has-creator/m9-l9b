NER_LABEL_TO_KG_TYPE: dict[str, set[str]] = {
    "PERSON": {"Author"},
    "ORG": {"Author"},
    "GPE": {"Cuisine"},
    "FOOD": {"Ingredient", "Cuisine"},
    "INGREDIENT": {"Ingredient"},
    "TECHNIQUE": {"Technique"},
}


def disambiguate(
    driver,
    candidates_: list[dict],
    ner_label: str,
    doc_resolved: list,
) -> tuple[dict | None, str]:
    if not candidates_:
        return (None, "nil-no-candidates")

    if len(candidates_) == 1:
        return (candidates_[0], "resolved-unique")

    # Signal 1 — type filter
    compatible = NER_LABEL_TO_KG_TYPE.get(ner_label, set())
    type_matches = [c for c in candidates_ if set(c["labels"]) & compatible]
    if len(type_matches) == 1:
        return (type_matches[0], "resolved-by-type")

    surviving = type_matches if type_matches else candidates_

    # Signal 2 — hierarchical traversal
    hier_query = """
        MATCH (c:Entity {id: $cand_id})
        MATCH (c)-[:SUBCLASS_OF*0..]->(ancestor:Entity)
        RETURN collect(labels(ancestor)) AS ancestor_labels
    """
    hier_matches = []
    with driver.session() as session:
        for c in surviving:
            result = session.run(hier_query, cand_id=c["id"]).single()
            if result:
                all_labels = set()
                for label_list in result["ancestor_labels"]:
                    all_labels.update(label_list)
                all_labels.discard("Entity")
                if all_labels & compatible:
                    hier_matches.append(c)

    if len(hier_matches) == 1:
        return (hier_matches[0], "resolved-by-hierarchy")

    surviving = hier_matches if hier_matches else surviving

    # Signal 3 — co-occurrence
    resolved_ids = [r.predicted_node_id for r in doc_resolved if r.predicted_node_id]
    if resolved_ids:
        context_query = """
            MATCH (c:Entity {id: $cand_id})-[]-(neighbor:Entity)
            WHERE neighbor.id IN $resolved_ids
            RETURN count(neighbor) AS overlap
        """
        scores = []
        with driver.session() as session:
            for c in surviving:
                result = session.run(context_query, cand_id=c["id"], resolved_ids=resolved_ids).single()
                overlap = result["overlap"] if result else 0
                scores.append((overlap, c))

        scores.sort(key=lambda x: x[0], reverse=True)
        if scores and scores[0][0] > 0 and (len(scores) < 2 or scores[0][0] > scores[1][0]):
            return (scores[0][1], "resolved-by-context")

    return (None, "nil-ambiguous")