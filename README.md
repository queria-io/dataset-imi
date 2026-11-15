# dataset-imi

Queria のデータセット `imi`（IMI 共通語彙基盤 コア語彙）のリポジトリです。データセットの説明は [docs/index.md](docs/index.md) にあります。

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # fdl checkout → python main.py → fdl commit
```

PR では `Build` ワークフローが、公開せずにパイプラインと `dbt build` だけを実行します。
