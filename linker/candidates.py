def candidates(driver, surface: str) -> list[dict]:
    query = """
        MATCH (n:Entity)
        WHERE toLower(n.name) = toLower($surface)
        RETURN n.id AS id, n.name AS name, labels(n) AS labels
    """
    with driver.session() as session:
        results = session.run(query, surface=surface)
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "labels": [l for l in row["labels"] if l != "Entity"]
            }
            for row in results
        ]