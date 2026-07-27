"""Run a .rq SPARQL query file against the local Fuseki endpoint and print results as a table."""
import sys
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON

FUSEKI_ENDPOINT = "http://fuseki:3030/paper-kg/sparql"


def run_query(query_path: str) -> None:
    query_text = Path(query_path).read_text(encoding="utf-8")

    sparql = SPARQLWrapper(FUSEKI_ENDPOINT)
    sparql.setQuery(query_text)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    bindings = results["results"]["bindings"]
    if not bindings:
        print("(no results)")
        return

    variables = results["head"]["vars"]
    print(" | ".join(variables))
    print("-" * 60)
    for row in bindings:
        # strip namespace prefix for readability, e.g. keep only "hindsightPaper"
        values = [row[v]["value"].split("#")[-1] if v in row else "" for v in variables]
        print(" | ".join(values))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_sparql.py <path-to-.rq-file>")
        sys.exit(1)
    run_query(sys.argv[1])