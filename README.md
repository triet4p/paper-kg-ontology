# Paper Knowledge Graph / Ontology

Dự án thực hành Ontology: OWL2 RL + RDF (Turtle) + Apache Jena + TDB2 + SHACL + SPARQL,
với use case là Knowledge Graph cho một tập paper nghiên cứu (memory / cognitive architecture).

## Kiến trúc

- **fuseki** (container): chạy Fuseki server, chứa TDB2 dataset + reasoner OWL2 RL,
  và có sẵn CLI tools (`riot`, `tdb2.tdbloader`, `shacl`) để thao tác trực tiếp.
- **client** (container): chạy script Python, giao tiếp với Fuseki qua SPARQL HTTP protocol.

## Cấu trúc thư mục

- `ontology/paper-kg.ttl` — TBox (schema: class, property)
- `ontology/instances.ttl` — ABox (dữ liệu paper/author cụ thể)
- `shapes/` — SHACL shapes để validate dữ liệu
- `queries/` — các file SPARQL (`.rq`) tái sử dụng
- `scripts/` — script Python (load data, chạy query)
- `tdb2-data/` — volume lưu TDB2 store (không commit vào git)

## Chạy dự án

\`\`\`bash
docker compose build
docker compose up -d fuseki
docker compose exec fuseki riot --version      # kiểm tra CLI có sẵn
\`\`\`

Fuseki UI: http://localhost:3030

## Yêu cầu

- Docker + Docker Compose
- Apache Jena 6.1.0 (Java 21 runtime, đã đóng gói sẵn trong image)