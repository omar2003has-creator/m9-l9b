from linker.types import LinkResult, GoldSpan

def score(predictions: list[LinkResult], gold: list[GoldSpan]) -> dict:
    gold_index = {(g.doc_id, g.start, g.end): g for g in gold}
    
    gold_docs = {}
    for g in gold:
        gold_docs.setdefault(g.doc_id, []).append(g)

    pred_index = {}
    for p in predictions:
        key = (p.doc_id, p.start, p.end)
        if key in gold_index:
            pred_index[key] = p

    per_doc_metrics = []

    for doc_id, doc_gold in gold_docs.items():
        if not doc_gold:
            continue

        tp, fp, fn = 0, 0, 0

        for g in doc_gold:
            key = (g.doc_id, g.start, g.end)
            p = pred_index.get(key)
            gold_is_nil = g.gold_node_id is None

            if gold_is_nil:
                if p and p.predicted_node_id is not None:
                    fp += 1
            else:
                if p is None or p.predicted_node_id is None:
                    fn += 1
                elif p.predicted_node_id == g.gold_node_id and p.predicted_type_label == g.gold_type_label:
                    tp += 1
                else:
                    fp += 1
                    fn += 1

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        per_doc_metrics.append((prec, rec, f1))

    if not per_doc_metrics:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    n = len(per_doc_metrics)
    return {
        "precision": sum(m[0] for m in per_doc_metrics) / n,
        "recall": sum(m[1] for m in per_doc_metrics) / n,
        "f1": sum(m[2] for m in per_doc_metrics) / n,
    }