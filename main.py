"""IMI 共通語彙基盤 コア語彙データパイプライン。

1. imi: コア語彙 2.4.2 の RDF スキーマを CSV にする
2. dbt: dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.imi import download_imi

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        result = dbt.invoke(command)
        if not result.success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def main():
    logger.info("1/2: imi (IMI コア語彙)")
    download_imi()

    logger.info("2/2: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
