# app/services.py

import httpx
import os
from dotenv import load_dotenv
from . import schemas

# .envファイルから環境変数を読み込む
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"

class GoogleSearchService:
    @staticmethod
    def _generate_query(req: schemas.SuggestionRequest) -> str:
        """リクエスト情報から検索クエリを生成する"""
        
        # 空き時間を計算（時間単位）
        duration_hours = (req.free_time_end - req.free_time_start).total_seconds() / 3600
        
        query_parts = []
        
        # 場所の情報があればクエリに追加
        locations = []
        if req.prev_event and req.prev_event.location:
            locations.append(req.prev_event.location)
        if req.next_event and req.next_event.location:
            # 前後の場所が同じなら1つにまとめる
            if not req.prev_event or req.prev_event.location != req.next_event.location:
                 locations.append(req.next_event.location)

        if locations:
            query_parts.append(f"{'や'.join(locations)} 付近")

        # 予定内容の情報があればクエリに追加
        contents = []
        if req.prev_event and req.prev_event.content:
            contents.append(req.prev_event.content)
        if req.next_event and req.next_event.content:
            contents.append(req.next_event.content)
        
        if contents:
            query_parts.append(f"{'と'.join(contents)}に関連する")
            
        # 時間の情報をクエリに追加
        query_parts.append(f"{duration_hours:.1f}時間でできること")

        # シンプルなクエリを返す（ここは要件に合わせて高度化できます）
        if not query_parts:
            return "近くのおすすめスポット"

        return " ".join(query_parts)

    @staticmethod
    async def search_suggestions(req: schemas.SuggestionRequest) -> schemas.SuggestionResponse:
        if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
            raise ValueError("Google API Key or CSE ID is not set.")

        query = GoogleSearchService._generate_query(req)
        
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "num": 5  # 提案を5件取得
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(SEARCH_API_URL, params=params)
            response.raise_for_status() # エラーがあれば例外を発生
        
        data = response.json()
        suggestions = []
        if "items" in data:
            for item in data["items"]:
                suggestions.append(
                    schemas.Suggestion(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        snippet=item.get("snippet", "")
                    )
                )
        
        return schemas.SuggestionResponse(query=query, suggestions=suggestions)