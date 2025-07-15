# secretary-backend
Secretary App Project

## uvでの実行

### 依存関係の同期
`uv sync`

### 仮想環境のアクティベート
mac: `source .venv/bin/activate`  
win: `.venv/` 

### fastapiサーバの起動
`uvicorn app.main:app --reload`

## docker用実行コマンド
```bash
docker build -t secretary-backend .
docker run -p 8000:8000 secretary-backend
```