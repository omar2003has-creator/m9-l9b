"""Identity Discipline helpers.

In a property graph, identity is not free the way it is for RDF URIs.
Every KG node must carry a canonical id derived from (label, name) so that
two surface mentions of "orange" resolve to the same node iff they refer
to the same entity. The :Entity uniqueness constraint declared in
data/recipes_kg.cypher enforces this.

`canonical_id` is fully implemented — do not modify. `merge_entity` has
one TODO: produce the parameterized Cypher MERGE statement and bound
parameter dict for the (label, name) pair (gated by the Lab 9B
autograder under Gate 1b).
"""
import re


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def canonical_id(label: str, name: str) -> str:
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return f"{label.strip().lower()}:{slug}"


def merge_entity(label: str, name: str, extra_props: dict | None = None) -> tuple[str, dict]:
    extra_props = extra_props or {}
    node_id = canonical_id(label, name)

    set_clauses = ["n.name = $name"]
    for key in extra_props:
        set_clauses.append(f"n.{key} = ${key}")

    cypher = f"MERGE (n:{label}:Entity {{id: $id}}) SET {', '.join(set_clauses)}"

    params = {"id": node_id, "name": name, **extra_props}

    return (cypher, params)