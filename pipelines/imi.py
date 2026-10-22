"""IMI 共通語彙基盤のコア語彙を取り出す。

コア語彙は 2.4.2（2019-02）が最後の版で、それ以降は更新されていない。版を固定し、
配布されている RDF のスキーマ（schema_rdf.zip）を読んで、語ごとに 1 行の CSV にする。

出力:
- data/imi/term.csv（1行 = コア語彙の 1 語。クラスとプロパティ）
- data/imi/class_property.csv（1行 = クラスが持てるプロパティ 1 つ。OWL の制約から取る）

データソース: IMI 情報共有基盤 共通語彙基盤 コア語彙 2.4.2
https://imi.go.jp/core/core242/
"""

import csv
import io
import logging
import urllib.request
import zipfile
from collections import Counter
from functools import reduce
from pathlib import Path

from rdflib import OWL, RDF, RDFS, XSD, BNode, Graph, Literal, Namespace, URIRef

logger = logging.getLogger("pipelines")

VERSION = "2.4.2"
SCHEMA_URL = "https://imi.go.jp/ns/core/242/schema_rdf.zip"
IC = Namespace("http://imi.go.jp/ns/core/rdf#")
SCHEMA = Namespace("http://schema.org/")
DCT = Namespace("http://purl.org/dc/terms/")
OUTPUT_DIR = Path("data/imi")

KINDS = {
    RDFS.Class: "class",
    OWL.Class: "class",
    OWL.DeprecatedClass: "class",
    RDF.Property: "property",
    OWL.ObjectProperty: "property",
    OWL.DatatypeProperty: "property",
    OWL.DeprecatedProperty: "property",
    RDFS.Datatype: "datatype",
}
DEPRECATED = {OWL.DeprecatedClass, OWL.DeprecatedProperty}
# zip には同じスキーマが ttl・xml・jsonld で入っている。1 つだけ、この順で選んで読む
FORMATS = {".ttl": "turtle", ".rdf": "xml", ".owl": "xml", ".xml": "xml", ".jsonld": "json-ld"}
PREFIXES = {str(IC): "ic:", str(XSD): "xsd:"}


def download(url: str = SCHEMA_URL) -> bytes:
    with urllib.request.urlopen(url) as res:
        return res.read()


def load_graph(archive: bytes) -> Graph:
    graph = Graph()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        logger.info("  zip の中身: %s", z.namelist())
        candidates = [n for n in z.namelist() if Path(n).suffix.lower() in FORMATS]
        if not candidates:
            raise SystemExit("zip に RDF のファイルが無い")
        name = min(candidates, key=lambda n: list(FORMATS).index(Path(n).suffix.lower()))
        logger.info("  読むファイル: %s", name)
        graph.parse(data=z.read(name), format=FORMATS[Path(name).suffix.lower()])
    return graph


def text(graph: Graph, subject, predicates, lang: str) -> str:
    values = [o for p in predicates for o in graph.objects(subject, p) if isinstance(o, Literal)]
    # 日本語は言語タグの無いものも日本語とみなす
    picked = [o for o in values if o.language == lang] or (
        [o for o in values if o.language is None] if lang == "ja" else []
    )
    return str(picked[0]) if picked else ""


def refs(graph: Graph, subject, predicates) -> str:
    # 複数あるものは「|」でつなぐ（domain が複数のクラスのプロパティなど）
    return "|".join(sorted({local(o) for p in predicates for o in graph.objects(subject, p) if isinstance(o, URIRef)}))


def local(uri: URIRef) -> str:
    s = str(uri)
    return next((prefix + s.removeprefix(ns) for ns, prefix in PREFIXES.items() if s.startswith(ns)), s)


def term_rows(graph: Graph) -> list[dict]:
    subjects = sorted({s for s in graph.subjects() if isinstance(s, URIRef) and str(s).startswith(str(IC))})

    def row(s: URIRef) -> dict:
        rdf_types = set(graph.objects(s, RDF.type))
        types = {KINDS.get(t, local(t)) for t in rdf_types}
        return {
            "version": VERSION,
            "uri": str(s),
            "name": str(s).removeprefix(str(IC)),
            "kind": "|".join(sorted(types)),
            "deprecated": bool(rdf_types & DEPRECATED),
            "label_ja": text(graph, s, [RDFS.label], "ja"),
            "label_en": text(graph, s, [RDFS.label], "en"),
            "description": text(graph, s, [RDFS.comment, DCT.description], "ja"),
            # subClassOf には OWL の制約（空白ノード）も入っているので、名前のあるクラスだけを拾う
            "parent": refs(graph, s, [RDFS.subClassOf, RDFS.subPropertyOf]),
            "domain": refs(graph, s, [RDFS.domain, SCHEMA.domainIncludes]),
            "range": refs(graph, s, [RDFS.range, SCHEMA.rangeIncludes]),
        }

    return [row(s) for s in subjects]


def class_property_rows(graph: Graph) -> list[dict]:
    # クラスが持てるプロパティは rdfs:subClassOf の先の owl:Restriction に書かれている
    #   ic:住所型 rdfs:subClassOf [ owl:onProperty ic:表記 ; owl:maxQualifiedCardinality 1 ; owl:onDataRange xsd:string ]
    def row(cls: URIRef, r: BNode) -> dict | None:
        prop = graph.value(r, OWL.onProperty)
        if not isinstance(prop, URIRef):
            return None
        value_type = next(
            (graph.value(r, p) for p in (OWL.onClass, OWL.onDataRange, OWL.allValuesFrom) if graph.value(r, p) is not None),
            None,
        )
        cardinality = next(
            (graph.value(r, p) for p in (OWL.maxQualifiedCardinality, OWL.maxCardinality) if graph.value(r, p) is not None),
            None,
        )
        return {
            "version": VERSION,
            "class_name": local(cls),
            "property_name": local(prop),
            "value_type": local(value_type) if isinstance(value_type, URIRef) else "",
            "max_cardinality": "" if cardinality is None else str(cardinality),
        }

    pairs = [
        (cls, r) for cls, r in graph.subject_objects(RDFS.subClassOf)
        if isinstance(cls, URIRef) and str(cls).startswith(str(IC)) and isinstance(r, BNode)
    ]
    rows = [x for x in (row(cls, r) for cls, r in pairs) if x]
    # 同じクラスとプロパティの組に制約が 2 つ（型と個数）分かれて書かれることがあるので畳む
    def merge(acc: dict, r: dict) -> dict:
        key = (r["class_name"], r["property_name"])
        old = acc.get(key, {})
        return {**acc, key: {**r, **{k: v for k, v in old.items() if v and not r[k]}}}

    merged = reduce(merge, rows, {})
    return sorted(merged.values(), key=lambda r: (r["class_name"], r["property_name"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def download_imi(output_dir: Path = OUTPUT_DIR) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    graph = load_graph(download())
    # 形が想定と違ったときに原因を追えるよう、述語の内訳を残す
    logger.info("  述語: %s", Counter(local(p) for p in graph.predicates()).most_common())
    rows = term_rows(graph)
    if not rows:
        raise SystemExit(f"{SCHEMA_URL}: ic: の語が 1 つも取れなかった")
    write_csv(output_dir / "term.csv", rows)
    logger.info("  term: %d 語（%s）", len(rows), Counter(r["kind"] for r in rows))
    links = class_property_rows(graph)
    write_csv(output_dir / "class_property.csv", links)
    logger.info("  class_property: %d 行", len(links))
    return len(rows)
