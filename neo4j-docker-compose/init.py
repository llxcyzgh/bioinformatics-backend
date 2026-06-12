import json
import os
import time

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_AUTH = os.getenv("NEO4J_AUTH", "neo4j/password")
DATA_FILE = os.getenv("DATA_FILE", "/data/data.json")

if "/" not in NEO4J_AUTH:
    raise ValueError("NEO4J_AUTH must be in the format 'username/password'")

username, password = NEO4J_AUTH.split("/", 1)


def wait_for_neo4j(driver, retries: int = 30, delay: float = 1.0) -> None:
    for i in range(retries):
        try:
            with driver.session() as session:
                session.run("RETURN 1")
                print("Neo4j is ready.")
                return
        except Exception as e:
            print(f"Waiting for Neo4j... ({i + 1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Neo4j did not become ready in time.")


def main() -> None:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(username, password))
    wait_for_neo4j(driver)

    with driver.session() as session:
        print("Wiping existing data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("Creating nodes...")
        for node in data.get("nodes", []):
            label = node["label"]
            props = {**node.get("properties", {}), "id": node["id"]}
            query = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
            session.run(query, id=node["id"], props=props)

        print("Creating relationships...")
        for rel in data.get("relationships", []):
            rel_type = rel["type"]
            props = rel.get("properties", {})
            query = (
                f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props"
            )
            session.run(
                query,
                from_id=rel["from"],
                to_id=rel["to"],
                props=props,
            )

        result = session.run("MATCH (n) RETURN count(n) AS count").single()
        print(f"Initialized Neo4j with {result['count']} nodes.")

    driver.close()


if __name__ == "__main__":
    main()
