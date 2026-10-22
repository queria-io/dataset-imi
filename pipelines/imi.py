"""IMI 共通語彙基盤のコア語彙を取り出す。

コア語彙は 2.4.2（2019-02）が最後の版で、それ以降は更新されていない。版を固定し、
配布されている RDF のスキーマ（schema_rdf.zip）を読んで、語ごとに 1 行の CSV にする。

出力:
- data/imi/term.csv（1行 = コア語彙の 1 語。クラスとプロパティ）

データソース: IMI 情報共有基盤 共通語彙基盤 コア語彙 2.4.2
https://imi.go.jp/core/core242/
"""

import csv
import io
import logging
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace, URIRef

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
    RDF.Property: "property",
    OWL.ObjectProperty: "property",
    OWL.DatatypeProperty: "property",
}
FORMATS = {".rdf": "xml", ".owl": "xml", ".xml": "xml", ".ttl": "turtle", ".jsonld": "json-ld", ".nt": "nt"}


def download(url: str = SCHEMA_URL) -> bytes:
    with urllib.request.urlopen(url) as res:
        return res.read()


def load_graph(archive: bytes) -> Graph:
    graph = Graph()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names = [n for n in z.namelist() if Path(n).suffix.lower() in FORMATS]
        logger.info("  zip の中身: %s", z.namelist())
        for name in names:
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
    return "ic:" + s.removeprefix(str(IC)) if s.startswith(str(IC)) else s


def term_rows(graph: Graph) -> list[dict]:
    subjects = sorted({s for s in graph.subjects() if isinstance(s, URIRef) and str(s).startswith(str(IC))})

    def row(s: URIRef) -> dict:
        types = {KINDS.get(t, local(t)) for t in graph.objects(s, RDF.type)}
        return {
            "version": VERSION,
            "uri": str(s),
            "name": str(s).removeprefix(str(IC)),
            "kind": "|".join(sorted(types)),
            "label_ja": text(graph, s, [RDFS.label], "ja"),
            "label_en": text(graph, s, [RDFS.label], "en"),
            "description": text(graph, s, [RDFS.comment, DCT.description], "ja"),
            "parent": refs(graph, s, [RDFS.subClassOf, RDFS.subPropertyOf]),
            "domain": refs(graph, s, [RDFS.domain, SCHEMA.domainIncludes]),
            "range": refs(graph, s, [RDFS.range, SCHEMA.rangeIncludes]),
        }

    return [row(s) for s in subjects]


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
    return len(rows)
