"""Add a new Paper (and related entities) into the Fuseki dataset via SPARQL UPDATE.

Design choice: entity identity is resolved deterministically by slugifying the
given name into an IRI local name (e.g. "Yann LeCun" -> :yannLecun). This means
calling add_paper() twice with the same author name reuses the same :Author
instance instead of creating a duplicate — a minimal stand-in for real entity
resolution (which in production would query existing rdfs:label / owl:sameAs).
"""
import re
from dataclasses import dataclass, field
from SPARQLWrapper import SPARQLWrapper, POST

UPDATE_ENDPOINT = "http://fuseki:3030/paper-kg/update"
PREFIX = "http://example.triet4p.org/paper-kg#"


def slugify(name: str) -> str:
    """Convert a human name/title into a camelCase local IRI name."""
    words = re.sub(r"[^a-zA-Z0-9 ]", "", name).split()
    if not words:
        raise ValueError(f"cannot slugify empty name: {name!r}")
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def escape_literal(text: str) -> str:
    """Escape characters that would break a Turtle string literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


@dataclass
class PaperInput:
    title: str
    year: int
    first_author: str
    co_authors: list[str] = field(default_factory=list)
    method_name: str | None = None          # core method this paper proposes
    proposes_benchmark: str | None = None   # benchmark this paper introduces
    evaluates_on: list[str] = field(default_factory=list)  # existing benchmarks used
    concept: str | None = None
    venue_name: str = "arXiv preprint"
    venue_type: str = "Preprint"            # one of: Preprint, Conference, Journal


def build_insert_query(paper: PaperInput) -> str:
    paper_iri = slugify(paper.title)
    first_author_iri = slugify(paper.first_author)
    co_author_iris = [slugify(a) for a in paper.co_authors]
    venue_iri = slugify(paper.venue_name)

    lines = [f"PREFIX : <{PREFIX}>", "INSERT DATA {"]

    # --- Author declarations (safe to redeclare — RDF is set-based, no duplicate triples) ---
    lines.append(f"  :{first_author_iri} a :Author .")
    for iri in co_author_iris:
        lines.append(f"  :{iri} a :Author .")

    # --- Venue ---
    lines.append(f"  :{venue_iri} a :{paper.venue_type} .")

    # --- Concept ---
    if paper.concept:
        concept_iri = slugify(paper.concept)
        lines.append(f"  :{concept_iri} a :Concept .")

    # --- Method ---
    if paper.method_name:
        method_iri = slugify(paper.method_name)
        lines.append(f"  :{method_iri} a :Method .")

    # --- Benchmarks (proposed + evaluated-on) ---
    if paper.proposes_benchmark:
        bench_iri = slugify(paper.proposes_benchmark)
        lines.append(f"  :{bench_iri} a :Benchmark .")
    eval_bench_iris = [slugify(b) for b in paper.evaluates_on]
    for iri, name in zip(eval_bench_iris, paper.evaluates_on):
        lines.append(f"  :{iri} a :Benchmark .")

    # --- Paper itself ---
    lines.append(f'  :{paper_iri} a :Paper ;')
    lines.append(f'    :title "{escape_literal(paper.title)}" ;')
    lines.append(f'    :year "{paper.year}"^^xsd:gYear ;')
    lines.append(f'    :hasFirstAuthor :{first_author_iri} ;')
    if co_author_iris:
        co_list = ", ".join(f":{i}" for i in co_author_iris)
        lines.append(f'    :hasCoAuthor {co_list} ;')
    lines.append(f'    :publishedIn :{venue_iri} ;')
    if paper.method_name:
        lines.append(f'    :proposesMethod :{slugify(paper.method_name)} ;')
    if paper.proposes_benchmark:
        lines.append(f'    :proposesBenchmark :{slugify(paper.proposes_benchmark)} ;')
    if eval_bench_iris:
        eval_list = ", ".join(f":{i}" for i in eval_bench_iris)
        lines.append(f'    :evaluatesOn {eval_list} ;')
    if paper.concept:
        lines.append(f'    :relatesToConcept :{slugify(paper.concept)} ;')

    lines[-1] = lines[-1].rstrip(" ;") + " ."  # close the last predicate list with a period
    lines.append("}")

    # PREFIX for xsd used inside the block
    return "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n" + "\n".join(lines)


def add_paper(paper: PaperInput) -> None:
    query = build_insert_query(paper)
    sparql = SPARQLWrapper(UPDATE_ENDPOINT)
    sparql.setMethod(POST)
    sparql.setQuery(query)
    sparql.query()
    print(f"Inserted paper: {paper.title}")


if __name__ == "__main__":
    # Example: add a 5th paper without touching any .ttl file
    example = PaperInput(
        title="Example New Memory Paper",
        year=2026,
        first_author="Jane Doe",
        co_authors=["John Smith"],
        method_name="graph attention retrieval",
        evaluates_on=["LongMemEval"],   # reuses existing :longMemEval instance (same slug)
        concept="agentic memory",       # reuses existing :agenticMemory instance
        venue_name="arXiv preprint",    # reuses existing :arxivPreprint instance
        venue_type="Preprint",
    )
    add_paper(example)