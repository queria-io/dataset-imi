# IMI 共通語彙基盤 コア語彙

[IMI 共通語彙基盤](https://imi.go.jp/core/)のコア語彙 2.4.2 を、SQL で検索できるテーブルにしたデータセットです。住所・施設・組織・人などを記述するための語（クラスとプロパティ）を、恒久的な URI・ラベル・説明・定義域・値域とともに収録しています。

列や項目の意味を URI で指したいとき、GIF の項目の元になった語を確認したいときに使います。列名や項目の英語名を決めるときは、こちらではなく [gif データセット](https://github.com/queria-io/dataset-gif)（デジタル庁の政府相互運用性フレームワーク）を使ってください。GIF の項目の多くはこの語彙を参考元にしています。

## 出典と利用条件

[IMI 共通語彙基盤 コア語彙 2.4.2](https://imi.go.jp/core/core242/) の RDF スキーマ（`https://imi.go.jp/ns/core/242/schema_rdf.zip` の Turtle）を読み、名前空間 `http://imi.go.jp/ns/core/rdf#` の語を 1 語 1 行のテーブルと、クラスが持てるプロパティのテーブルに加工しています。

- IMI のサイトの内容は、個別の指定がない限り CC0 1.0 です
- コア語彙は 2019 年の 2.4.2 が最後のバージョンで、それ以降は更新されていません

## テーブル

| テーブル | 内容 |
| --- | --- |
| `vocab.term` | コア語彙の語。1 行が 1 語（クラス・プロパティ・データ型、309 語） |
| `vocab.class_property` | クラスが持てるプロパティ。1 行がクラスとプロパティの組 |

## 使い方

名前が「コード」で終わる語:

```sql
SELECT name, kind, label_ja, domain, range
FROM imi.vocab.term
WHERE name LIKE '%コード';
```

## 収録範囲の注意

- 語の名前は日本語だけです。英語のラベル（`label_en`）は多くの語にありません
- `vocab.class_property` は RDF スキーマの `owl:Restriction` から作っています。上位のクラスから受け継ぐプロパティは、上位のクラスの行にだけあります（住所型の行に事物型のプロパティは出ません）
- `parent`・`domain`・`range` は、値が複数あるとき `|` 区切りで入っています

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # queria sync -- python main.py
```

PR では `Build` ワークフローが、公開せずにパイプラインと `dbt build` だけを実行します。
