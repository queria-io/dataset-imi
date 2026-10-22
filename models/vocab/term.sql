{# IMI 共通語彙基盤 コア語彙 2.4.2 の語。1行が1語（クラスかプロパティ）。
   pipelines/imi.py が配布 RDF から data/imi/term.csv に書き出す。 #}

select
    version,
    uri,
    name,
    kind,
    nullif(label_ja, '') as label_ja,
    nullif(label_en, '') as label_en,
    nullif(description, '') as description,
    nullif(parent, '') as parent,
    nullif(domain, '') as domain,
    nullif(range, '') as range
from read_csv('data/imi/term.csv', header = true, all_varchar = true)
