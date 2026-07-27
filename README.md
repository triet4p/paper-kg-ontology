# Paper Knowledge Graph / Ontology

Dự án thực hành Ontology: OWL2 RL + RDF (Turtle) + Apache Jena + TDB2 + SHACL + SPARQL,
với use case là Knowledge Graph cho một tập paper nghiên cứu (memory / cognitive architecture).

## Kiến trúc

```
TDB2 (raw data)
  └─► [OWLMicroFBRuleReasoner]          ← Layer 1: subClassOf, subPropertyOf, domain/range
        └─► [GenericRuleReasoner]        ← Layer 2: custom rules (property chain)
              └─► SPARQL endpoint        ← /paper-kg/sparql
```

- **fuseki** (container): Apache Jena Fuseki 6.1.0, chạy TDB2 dataset với reasoner pipeline 2 lớp.
- **client** (container): chạy script Python, giao tiếp với Fuseki qua SPARQL HTTP protocol.

### Reasoner pipeline

Fuseki config (`config/fuseki-assembler.ttl`) sử dụng 2 lớp `InfModel` lồng nhau:

| Lớp | Reasoner | Xử lý |
|-----|----------|-------|
| `<#owlLayer>` | `OWLMicroFBRuleReasoner` | `rdfs:subClassOf`, `rdfs:subPropertyOf`, `rdfs:domain`/`range` |
| `<#inferredModel>` | `GenericRuleReasoner` + `config/cites-rules.rules` | `owl:propertyChainAxiom` (`:citesTransitively`) |

Lý do: Jena không hỗ trợ `owl:propertyChainAxiom` trong các reasoner built-in (Micro/Mini/Full) —
đây là giới hạn của rule-based reasoner, khác với reasoner tableau đầy đủ như Pellet/HermiT.
Giải pháp là chồng `GenericRuleReasoner` với custom rules lên kết quả của `OWLMicroFBRuleReasoner`,
giữ nguyên toàn bộ suy luận RDFS/OWL cơ bản.

`GenericRuleReasoner` dùng **RETE engine** — suy luận không chỉ chạy 1 lần lúc startup
(materialize toàn bộ ra RAM) mà còn **incremental**: khi INSERT triple mới qua SPARQL UPDATE
lúc runtime, engine tự động chạy lại những rule bị ảnh hưởng, inference mới xuất hiện ngay
không cần restart.

## Cấu trúc thư mục

```
├── ontology/
│   ├── paper-kg.ttl              ← TBox (schema: class, property, axioms)
│   └── instances.ttl             ← ABox (dữ liệu paper/author/method/benchmark)
├── config/
│   ├── fuseki-assembler.ttl      ← Fuseki assembler config (reasoner pipeline 2 lớp)
│   └── cites-rules.rules         ← Custom rules cho :citesTransitively (property chain)
├── shapes/
│   └── paper-kg-shapes.ttl       ← SHACL shapes để validate dữ liệu
├── queries/
│   ├── q1-critical-concept-overlap.rq   ← Paper có chung concept
│   ├── q2-involves-method-inferred.rq   ← Suy luận subPropertyOf (:involvesMethod)
│   ├── q3-venue-hierarchy.rq            ← Venue với type hierarchy
│   └── q4-cites-transitive.rq           ← Suy luận property chain (:citesTransitively)
├── scripts/
│   ├── run_sparql.py              ← Chạy file .rq từ client container
│   └── add_paper.py               ← Thêm paper mới qua SPARQL UPDATE (không cần sửa .ttl)
├── docker/
│   ├── fuseki/Dockerfile          ← Jena 6.1.0 + Fuseki 6.1.0 (eclipse-temurin:21-jre)
│   └── client/Dockerfile          ← Python 3.12 + SPARQLWrapper
├── docker-compose.yml
├── tdb2-data/                     ← Volume: TDB2 store (không commit vào git)
└── README.md
```

## Yêu cầu

- Docker + Docker Compose

## Bắt đầu

### 1. Build images

```bash
docker compose build
```

### 2. Load dữ liệu vào TDB2

```bash
# Xóa database cũ (nếu có) và load lại từ file .ttl
rm -rf tdb2-data/databases/paper-kg

docker compose run --rm fuseki \
  tdb2.tdbloader --loc /data/fuseki-base/databases/paper-kg \
  /data/ontology/paper-kg.ttl /data/ontology/instances.ttl
```

### 3. Khởi động Fuseki

```bash
docker compose up -d fuseki
```

Kiểm tra log khởi động:

```bash
docker compose logs fuseki
# Apache Jena Fuseki 6.1.0
# Database: /paper-kg
# Start Fuseki
```

Fuseki UI: **http://localhost:3030**

### 4. Dừng

```bash
docker compose down
```

## Load lại dữ liệu (sau khi sửa ontology)

```bash
docker compose down
rm -rf tdb2-data/databases/paper-kg
docker compose run --rm fuseki tdb2.tdbloader --loc /data/fuseki-base/databases/paper-kg /data/ontology/paper-kg.ttl /data/ontology/instances.ttl
docker compose up -d fuseki
```

Hoặc gộp thành 1 dòng:

```powershell
docker compose down; rm -r -fo tdb2-data/databases/paper-kg; docker compose run --rm fuseki tdb2.tdbloader --loc /data/fuseki-base/databases/paper-kg /data/ontology/paper-kg.ttl /data/ontology/instances.ttl; docker compose up -d fuseki
```

## Chạy SPARQL query

### Từ command line (curl)

```bash
curl -s -G "http://localhost:3030/paper-kg/sparql" \
  --data-urlencode "query=PREFIX : <http://example.triet4p.org/paper-kg#> SELECT ?a ?aLabel ?c ?cLabel WHERE { ?a :citesTransitively ?c . ?a :title ?aLabel . ?c :title ?cLabel . }" \
  -H "Accept: application/sparql-results+json"
```

### Từ client container (file .rq)

```bash
docker compose run --rm client python run_sparql.py /app/queries/q2-involves-method-inferred.rq
```

### Từ Fuseki UI

Mở **http://localhost:3030** → chọn dataset `paper-kg` → tab **Query**.

## Các query mẫu

| File | Mô tả | Suy luận |
|------|-------|----------|
| `q1-critical-concept-overlap.rq` | Tìm cặp paper chia sẻ cùng concept | Không |
| `q2-involves-method-inferred.rq` | Method của từng paper qua `:involvesMethod` | `rdfs:subPropertyOf` |
| `q3-venue-hierarchy.rq` | Venue của paper với subclass (Conference/Journal/Preprint) | `rdfs:subClassOf` |
| `q4-cites-transitive.rq` | Citation transitively: 1-hop + 2-hop suy luận | `owl:propertyChainAxiom` (custom rules) |

Kết quả mong đợi của `q4-cites-transitive.rq`:

| From | To | Kiểu |
|------|-----|------|
| Hindsight | HippoRAG | 1-hop (base case) |
| HippoRAG | Mem^p | 1-hop (base case) |
| Hindsight | **Mem^p** | 🔥 2-hop transitive inference |

## Thêm paper mới (không sửa file .ttl)

```bash
# Client container đã có Python + SPARQLWrapper
docker compose run --rm client python add_paper.py
```

Script `scripts/add_paper.py` dùng SPARQL UPDATE để insert paper mới vào dataset đang chạy.
Entity identity được resolve qua slug (camelCase từ tên) — gọi lại cùng tên sẽ reuse entity cũ.

Tuỳ chỉnh: sửa block `if __name__ == "__main__"` trong `add_paper.py` với thông tin paper của bạn.

### Inference incremental — không cần restart

Nhờ RETE engine của `GenericRuleReasoner`, khi thêm quan hệ `:cites` mới qua SPARQL UPDATE
lúc runtime, `:citesTransitively` được suy luận lại ngay lập tức. Ví dụ:

```bash
# Thêm citation mới trực tiếp qua SPARQL UPDATE
curl -X POST "http://localhost:3030/paper-kg/update" \
  --data-urlencode "update=
    PREFIX : <http://example.triet4p.org/paper-kg#>
    INSERT DATA { :amaBenchPaper :cites :memPPaper . }"

# Query ngay — amaBenchPaper :citesTransitively :memPPaper đã xuất hiện
docker compose run --rm client python run_sparql.py /app/queries/q4-cites-transitive.rq
```

> **Lưu ý:** Điều này chỉ áp dụng với SPARQL UPDATE vào dataset đang chạy. Nếu sửa file `.ttl`
> và dùng `tdb2.tdbloader`, bạn vẫn cần restart Fuseki (hoặc `docker compose down && up -d`)
> vì TDB2 được load lúc startup, không tự hot-reload từ file.

## SHACL Validation

Validate toàn bộ Paper instances:

```bash
docker compose run --rm fuseki \
  shacl validate --shapes /data/shapes/paper-kg-shapes.ttl \
  --data /data/ontology/instances.ttl
```

## Ontology summary

| Thực thể | Số lượng |
|----------|----------|
| Paper | 4 (Hindsight, HippoRAG, Mem^p, AMA-Bench) |
| Author | 12 |
| Method | 4 |
| Benchmark | 7 |
| Concept | 2 (longTermMemory, agenticMemory) |
| Venue | 3 (arXiv, NeurIPS 2024, ICML 2026) |

### Property hierarchy

```
:hasAuthor
  ├── :hasFirstAuthor
  └── :hasCoAuthor

:involvesMethod
  ├── :proposesMethod
  ├── :usesMethod
  └── :improvesMethod

:citesTransitively   ← owl:propertyChainAxiom ( :cites :cites )
```

### Citation graph

```
hindsightPaper ──:cites──► hippoRagPaper ──:cites──► memPPaper
     │                                                      ▲
     └──────────── :citesTransitively ──────────────────────┘
```
