# dataset-imi

[IMI 共通語彙基盤](https://imi.go.jp/core/)のコア語彙を Queria のカタログ
（[data.queria.io](https://data.queria.io/)）へ取り込むデータセットです。

## データ出典

コア語彙は 2019 年の 2.4.2 が最後の版です。配布されている RDF のスキーマ
（`https://imi.go.jp/ns/core/242/schema_rdf.zip`）を読み、名前空間
`http://imi.go.jp/ns/core/rdf#` の語を 1 語 1 行の表にします。

IMI のサイトの内容は、個別の指定が無い限り CC0 1.0 です。

列名や項目の英語名を決めるときは、こちらではなく [dataset-gif](https://github.com/queria-io/dataset-gif)
（デジタル庁の政府相互運用性フレームワーク）を使います。GIF の項目の多くはこの語彙を参考元にしていて、
こちらは語を URI で指したいときに使います。

## 収録テーブル

| テーブル | 内容 |
| --- | --- |
| `vocab.term` | コア語彙の語。1行が1語（クラスかプロパティ） |

```sql
SELECT name, kind, label_ja, domain, range
FROM imi.vocab.term
WHERE name LIKE '%コード';
```

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # queria sync -- python main.py
```

PR では `Build` ワークフローが、公開せずにパイプラインと `dbt build` だけを回します。
