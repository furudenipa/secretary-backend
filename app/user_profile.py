import os
import httpx
import json
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Sequence

from . import crud, models

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class UserProfileService:
    @staticmethod
    def _format_events_for_prompt(events: Sequence[models.Event]) -> str:
        """LLMへのプロンプト用に予定リストを整形する"""
        if not events:
            return "最近の予定はありません。"

        formatted_events = []
        for event in events:
            # 予定の所要時間を計算
            duration = event.end_time - event.start_time
            total_minutes = int(duration.total_seconds() // 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60

            duration_parts = []
            if hours > 0:
                duration_parts.append(f"{hours}時間")
            if minutes > 0:
                duration_parts.append(f"{minutes}分")

            duration_str = "".join(duration_parts) if duration_parts else "0分"

            # LLMに渡すテキストを整形
            event_text = f"- タイトル: {event.title}, 所要時間: {duration_str}, 場所: {event.location or '指定なし'}"
            if event.description is not None:
                event_text += f"（説明: {event.description}）"
            formatted_events.append(event_text)

        return "\n".join(formatted_events)

    @staticmethod
    def _create_prompt(events_summary: str) -> str:
        """LLMに送るプロンプトを作成する"""
        return f"""
あなたはユーザーの行動を分析するエキスパートです。
以下の予定リストから、ユーザーの傾向を分析し、指定されたJSON形式で結果を返してください。

# 予定リスト
{events_summary}

# 出力形式（JSON）
- `food_preferences`: 食事に関する傾向を分析してください。頻繁に登場する食事の種類（例：ラーメン、寿司、うどん）や、外食か自炊かなどの傾向をまとめてください。
- `activity_preferences`: 食事以外の活動に関する傾向を分析してください。趣味（例：読書、映画鑑賞）や学習、運動などの傾向をまとめてください。
- `outing_tendency`: 場所の情報から、ユーザーがインドア派かアウトドア派か、または特定の場所（例：カフェ、図書館）を好むかなどの外出傾向を分析してください。

# JSON出力例
{{
  "food_preferences": "ラーメンを週に2回ほど食べており、特に豚骨ラーメンを好む傾向があります。外食が中心のようです。",
  "activity_preferences": "週末に2時間程度の読書の時間を設けているほか、月に一度は映画館に足を運んでいます。",
  "outing_tendency": "都心部のカフェや書店への外出が多く、インドアでの活動を好む傾向が見られます。"
}}

# 分析結果（JSON）
"""

    @staticmethod
    async def generate_profile(db: AsyncSession) -> dict:
        """最近の予定からユーザープロフィールを生成する"""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API Key is not set. Please set the OPENAI_API_KEY environment variable.")

        recent_events = await crud.get_recently_updated_events(db=db, limit=20)
        if not recent_events:
            return {"food_preferences": "分析対象の予定が十分にありません。", "activity_preferences": "予定の履歴がありません。", "outing_tendency": "予定の履歴がありません。"}

        events_summary = UserProfileService._format_events_for_prompt(recent_events)
        prompt = UserProfileService._create_prompt(events_summary)

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "max_tokens": 1000,
            "temperature": 0.5,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            response_data = response.json()
            profile_json_string = response_data["choices"][0]["message"]["content"].strip()
            return json.loads(profile_json_string)
