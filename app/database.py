from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# SQLiteデータベースのURL
# 非同期用のドライバ `aiosqlite` を指定
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./calendar.db"

# 非同期エンジンを作成
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 非同期セッションを作成するためのメーカー
# autoflush=False, autocommit=False は非同期処理で標準的な設定
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)

# モデルクラスが継承するためのベースクラス
Base = declarative_base()

# DI (依存性注入) のための非同期セッション取得関数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
