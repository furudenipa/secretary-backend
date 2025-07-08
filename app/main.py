# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import events, suggestion, agent, planner, user_profile

# FastAPIアプリケーションインスタンスを作成
app = FastAPI(
    title="Calendar API",
    description="A calendar application backend with smart suggestions.",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing) の設定
# フロントエンド (React) からのアクセスを許可するために必要
origins = [
    "http://localhost:3000",  # React開発サーバーのデフォルトポート
    # 必要に応じて本番環境のフロントエンドURLを追加
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # すべてのHTTPメソッドを許可
    allow_headers=["*"], # すべてのヘッダーを許可
)

# ルーターをアプリケーションに登録
app.include_router(events.router)
app.include_router(suggestion.router)

app.include_router(agent.router)
app.include_router(planner.router)
app.include_router(user_profile.router)

@app.on_event("startup")
async def startup_event():
    # アプリケーション起動時にデータベーステーブルを作成する
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # 開発中にテーブルをリセットしたい場合
        await conn.run_sync(Base.metadata.create_all)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Calendar API!"}
