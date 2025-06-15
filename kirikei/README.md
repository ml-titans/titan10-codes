# titan10-llmo

* このフォルダは[uv](https://github.com/astral-sh/uv/tree/main)で管理しています。

### インストールと環境設定

```shell
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
cd <this directory>
uv sync # 環境構築
```

### 実行

* `.env`ファイルを作成し、本文中の環境変数を設定
* 以下のコマンドで実行

```shell
uv run top_services.py
```
