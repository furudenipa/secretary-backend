# Python 3.12をベースイメージとして使用
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# uvをインストール
RUN pip install uv

# プロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# uvを使用して依存関係をインストール
RUN uv sync --frozen

# アプリケーションのソースコードをコピー
COPY . .

# ポート8000を公開
EXPOSE 8000

# uvicornを使用してFastAPIアプリケーションを起動
# --host 0.0.0.0 でDockerの外部からアクセス可能にする
CMD ["uv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
