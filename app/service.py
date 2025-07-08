# app/services.py

# import httpx
import os
import json
import openai
from dotenv import load_dotenv
from tavily import TavilyClient
from . import schemas
from datetime import datetime

# .envファイルから環境変数を読み込む
load_dotenv()

# OpenAIクライアントを非同期で初期化
# APIキーが.envにあれば自動で読み込まれます
openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

class SuggestionService:
    @staticmethod
    def _create_tavily_query(req: schemas.SuggestionRequest) -> str:
        """ユーザーの状況からTavily検索用のクエリを生成する"""
        duration_hours = (req.free_time_end - req.free_time_start).total_seconds() / 3600
        
        # 場所の情報を優先
        locations = []
        if req.prev_event and req.prev_event.location:
            locations.append(req.prev_event.location)
        # 前後の場所が違う場合のみ追加
        if req.next_event and req.next_event.location:
            if not locations or locations[0] != req.next_event.location:
                locations.append(req.next_event.location)

        if locations:
            return f"{'または'.join(locations)}周辺で{duration_hours:.1f}時間で楽しめること"
        
        return "近くで短時間で楽しめるアクティビティ"

    @staticmethod
    def _create_openai_prompt(req: schemas.SuggestionRequest, tavily_context: str) -> str:
        """Tavilyの検索結果を元に、OpenAIへの詳細な指示プロンプトを生成する"""
        
        # 状況説明
        situation = f"""
        # ユーザーの状況
        - 直前の予定: {req.prev_event.content if req.prev_event else 'なし'}
        - 直前の予定の場所: {req.prev_event.location if req.prev_event else '不明'}
        - 空き時間の開始: {req.free_time_start.strftime('%H:%M')}
        - 空き時間の終了: {req.free_time_end.strftime('%H:%M')}
        - 直後の予定: {req.next_event.content if req.next_event else 'なし'}
        - 直後の予定の場所: {req.next_event.location if req.next_event else '不明'}

        # Web検索から得られた参考情報
        {tavily_context}
        """

        # 指示
        instruction = f"""
        # あなたのタスク
        あなたは非常に優秀な旅行プランナーです。上記の「ユーザーの状況」と「参考情報」を元に、空き時間を最大限に活用できる、具体的で実行可能なプランを1つ提案してください。
        以下の制約条件と出力形式を厳守してください。

        # 制約条件
        - 提案するアクティビティの開始から終了、そして次の予定への移動時間まで、すべてがユーザーの空き時間内に収まるように計画してください。
        - 移動時間は現実的な値を想定してください（例：徒歩10分、電車15分など）。
        - 提案する内容は、参考情報に基づいた、事実ベースのものにしてください。

        # 出力形式 (必ずこのJSON形式で出力してください)
        {{
          "title": "提案アクティビティの魅力的なタイトル",
          "description": "なぜこのプランがおすすめなのか、具体的な説明",
          "activity_start_time": "{req.free_time_start.strftime('%Y-%m-%dT%H:%M:%S')}",
          "activity_end_time": "{req.free_time_end.strftime('%Y-%m-%dT%H:%M:%S')}",
          "location": "アクティビティを行う具体的な場所",
          "estimated_cost": "おおよその費用（例：1,500円, 無料）",
          "travel_from_previous": {{
            "mode": "移動手段（徒歩、電車、バス、タクシーなど）",
            "duration_minutes": 15,
            "instructions": "前の予定の場所からの具体的な移動指示"
          }},
          "travel_to_next": {{
            "mode": "移動手段",
            "duration_minutes": 20,
            "instructions": "提案場所から次の予定の場所への具体的な移動指示"
          }},
          "source_link": "参考にした情報のURL"
        }}
        """
        return situation + instruction

    @staticmethod
    async def get_suggestions(req: schemas.SuggestionRequest) -> schemas.SuggestionResponse:
        if not openai_client.api_key or not tavily_client.api_key:
            raise ValueError("API Key is not set.")

        # 1. Tavilyで検索クエリを生成し、情報を検索
        tavily_query = SuggestionService._create_tavily_query(req)
        try:
            search_result = tavily_client.search(
                query=tavily_query,
                search_depth="advanced", # より詳細な検索
                max_results=5
            )
            # 検索結果を文脈として整形
            tavily_context = "\n".join([f"- {res['content']} (Source: {res['url']})" for res in search_result['results']])
        except Exception as e:
            raise ConnectionError(f"Tavily API search failed: {e}")

        # 2. OpenAIに渡すプロンプトを生成
        openai_prompt = SuggestionService._create_openai_prompt(req, tavily_context)

        # 3. OpenAI APIを呼び出し、詳細なプランを生成させる
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": openai_prompt}],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI API returned an empty response.")
            
            # JSONをパースし、Pydanticモデルに変換
            plan_data = json.loads(content)
            suggestion = schemas.Suggestion(**plan_data)
            
            return schemas.SuggestionResponse(
                search_query=tavily_query,
                suggestions=[suggestion] # 1つの詳細なプランを返す
            )
        except Exception as e:
            raise ConnectionError(f"OpenAI API call failed: {e}")

class MobilityAgent:
    @staticmethod
    async def _search_route_info(req: schemas.MobilityRequest) -> str:
        """Tavilyを使って、2地点間の移動に関するWeb情報を検索する"""
        origin = req.prev_event_location
        destination = req.next_event_location
        
        # 複数の角度から情報を集めるための検索クエリ
        queries = [
            f"{origin}から{destination}までの公共交通機関での行き方 料金と時間",
            f"{origin}から{destination}までの徒歩での時間と距離"
        ]
        
        # Tavilyの非同期検索を実行
        try:
            # searchメソッドは非同期ではないため、asyncio.to_threadで実行するのが望ましいですが
            # ここでは簡潔さのために直接呼び出します。
            # 大量の並列処理が必要な場合は to_thread の使用を検討してください。
            search_results = tavily_client.search(query="\n".join(queries), search_depth="basic", max_results=5)
            
            if not search_results or not search_results.get('results'):
                return "経路に関する有益なWeb情報は見つかりませんでした。"

            # 検索結果をLLMが読みやすいように要約する
            context = "\n".join([f"- {res['content']}" for res in search_results['results']])
            return f"# Web検索から得られた経路情報\n{context}"

        except Exception as e:
            print(f"Tavily API Error: {e}")
            return "経路に関するWeb情報の検索中にエラーが発生しました。"

    @staticmethod
    def _create_decision_prompt(search_context: str, req: schemas.MobilityRequest) -> str:
        """Web検索の結果を基に、LLMに意思決定を促すプロンプトを作成する"""
        
        # 移動に使える合計時間（分）を計算
        available_minutes = (req.next_event_start_time - req.prev_event_end_time).total_seconds() / 60

        prompt = f"""
        あなたはユーザーのパーソナルモビリティアドバイザーです。提供された「Web検索から得られた経路情報」と、ユーザーの「好み」を基に、最適な移動手段を推論してください。

        {search_context}

        # ユーザーの状況
        - 前の予定の終了時刻: {req.prev_event_end_time.strftime('%H:%M')}
        - 出発地: {req.prev_event_location}
        - 次の予定の開始時刻: {req.next_event_start_time.strftime('%H:%M')}
        - 目的地: {req.next_event_location}
        - 移動に使える合計時間: {available_minutes:.0f}分
        - ユーザーの好み: 「{req.user_preferences}」

        # あなたのタスク
        上記の全ての情報を注意深く分析し、ユーザーが「公共交通機関を使うべきか」を判断してください。
        Web検索の情報は不正確な場合があることを念頭に置き、常識的な範囲で推論してください。
        以下のJSON形式で、結論と理由を明確に出力してください。

        {{
          "use_public_transport": true,
          "recommended_mode": "公共交通機関",
          "reasoning": "Web検索の結果、公共交通機関を使えば約20分で到着できると推測されます。徒歩では間に合わないため、こちらを推奨します。",
          "estimated_time": 20,
          "estimated_cost": "約200円〜300円"
        }}
        """
        return prompt

    @staticmethod
    async def decide_mobility(req: schemas.MobilityRequest) -> schemas.MobilityResponse:
        """移動判別エージェントのメイン処理（Tavily + OpenAI版）"""
        if not openai_client.api_key or not tavily_client.api_key:
            raise ValueError("API Key is not set.")

        # 1. Tavilyで経路情報をWeb検索
        search_context = await MobilityAgent._search_route_info(req)

        # 2. OpenAIに渡すプロンプトを生成
        prompt = MobilityAgent._create_decision_prompt(search_context, req)

        # 3. OpenAI APIで推論・意思決定
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI API returned an empty response.")
            
            decision_data = json.loads(content)
            return schemas.MobilityResponse(**decision_data)

        except Exception as e:
            # エラーハンドリングを強化
            print(f"Error during OpenAI call or data parsing: {e}")
            raise ConnectionError(f"AI decision-making failed: {e}")

# class SuggestionService:
#     @staticmethod
#     def _generate_prompt(req: schemas.SuggestionRequest) -> str:
#         """リクエスト情報からOpenAIへのプロンプトを生成する"""
        
#         duration_minutes = int((req.free_time_end - req.free_time_start).total_seconds() / 60)
        
#         prompt_parts = ["あなたは優秀なアシスタントです。以下の状況に基づき、空き時間におすすめのアクティビティを提案してください。"]
        
#         # 状況説明
#         if req.prev_event:
#             prompt_parts.append(
#                 f"直前の予定は「{req.prev_event.content or '未設定'}」で、場所は「{req.prev_event.location or '未設定'}」です。"
#             )
#         if req.next_event:
#             prompt_parts.append(
#                 f"直後の予定は「{req.next_event.content or '未設定'}」で、場所は「{req.next_event.location or '未設定'}」です。"
#             )
        
#         prompt_parts.append(f"空き時間は約{duration_minutes}分です。")
        
#         # 場所の制約
#         locations = []
#         if req.prev_event and req.prev_event.location:
#             locations.append(req.prev_event.location)
#         if req.next_event and req.next_event.location:
#             if not req.prev_event or req.prev_event.location != req.next_event.location:
#                 locations.append(req.next_event.location)

#         if len(locations) == 1:
#             prompt_parts.append(f"場所は「{locations[0]}」周辺を想定してください。")
#         elif len(locations) > 1:
#             prompt_parts.append(f"場所は「{locations[0]}」から「{locations[1]}」への移動も考慮してください。")

#         # 指示
#         prompt_parts.append(
#             "\nこれらの情報を総合的に判断し、創造的で最適な提案を3つ、以下のJSON形式で出力してください。"
#         )
        
#         return "\n".join(prompt_parts)

#     @staticmethod
#     async def get_suggestions(req: schemas.SuggestionRequest) -> schemas.SuggestionResponse:
#         if not client.api_key:
#             raise ValueError("OpenAI API Key is not set.")

#         system_prompt = SuggestionService._generate_prompt(req)
        
#         # 出力してほしいJSONの形式をユーザーメッセージで補足
#         user_prompt = """
#         {
#           "suggestions": [
#             {
#               "title": "提案のタイトル",
#               "description": "提案内容の具体的な説明",
#               "link": "関連するURL（あれば）"
#             }
#           ]
#         }
#         """

#         try:
#             response = await client.chat.completions.create(
#                 model="gpt-4o",  # 最新モデル（またはgpt-3.5-turboなど）
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": user_prompt}
#                 ],
#                 temperature=0.7, # 創造性の度合い
#                 response_format={"type": "json_object"} # JSONモードを有効化
#             )
            
#             content = response.choices[0].message.content
#             if not content:
#                 raise ValueError("APIから空のレスポンスが返されました。")

#             # JSON文字列をパース
#             data = json.loads(content)
            
#             # Pydanticスキーマに変換
#             suggestions_data = data.get("suggestions", [])
#             suggestions = [schemas.Suggestion(**item) for item in suggestions_data]
            
#             # レスポンスを作成
#             query_summary = f"{int((req.free_time_end - req.free_time_start).total_seconds() / 60)}分の空き時間への提案"
#             return schemas.SuggestionResponse(query=query_summary, suggestions=suggestions)

#         except json.JSONDecodeError:
#             raise ValueError("APIが不正なJSON形式のレスポンスを返しました。")
#         except Exception as e:
#             # OpenAI APIのエラーなどを捕捉
#             print(f"OpenAI API error: {e}")
#             raise
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
# SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"



# class GoogleSearchService:
#     @staticmethod
#     def _generate_query(req: schemas.SuggestionRequest) -> str:
#         """リクエスト情報から検索クエリを生成する"""
        
#         # 空き時間を計算（時間単位）
#         duration_hours = (req.free_time_end - req.free_time_start).total_seconds() / 3600
        
#         query_parts = []
        
#         # 場所の情報があればクエリに追加
#         locations = []
#         if req.prev_event and req.prev_event.location:
#             locations.append(req.prev_event.location)
#         if req.next_event and req.next_event.location:
#             # 前後の場所が同じなら1つにまとめる
#             if not req.prev_event or req.prev_event.location != req.next_event.location:
#                  locations.append(req.next_event.location)

#         if locations:
#             query_parts.append(f"{'や'.join(locations)} 付近")

#         # 予定内容の情報があればクエリに追加
#         contents = []
#         if req.prev_event and req.prev_event.content:
#             contents.append(req.prev_event.content)
#         if req.next_event and req.next_event.content:
#             contents.append(req.next_event.content)
        
#         if contents:
#             query_parts.append(f"{'と'.join(contents)}に関連する")
            
#         # 時間の情報をクエリに追加
#         query_parts.append(f"{duration_hours:.1f}時間でできること")

#         # シンプルなクエリを返す（ここは要件に合わせて高度化できます）
#         if not query_parts:
#             return "近くのおすすめスポット"

#         return " ".join(query_parts)

#     @staticmethod
#     async def search_suggestions(req: schemas.SuggestionRequest) -> schemas.SuggestionResponse:
#         if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
#             raise ValueError("Google API Key or CSE ID is not set.")

#         query = GoogleSearchService._generate_query(req)
        
#         params = {
#             "key": GOOGLE_API_KEY,
#             "cx": GOOGLE_CSE_ID,
#             "q": query,
#             "num": 5  # 提案を5件取得
#         }
        
#         async with httpx.AsyncClient() as client:
#             response = await client.get(SEARCH_API_URL, params=params)
#             response.raise_for_status() # エラーがあれば例外を発生
        
#         data = response.json()
#         suggestions = []
#         if "items" in data:
#             for item in data["items"]:
#                 suggestions.append(
#                     schemas.Suggestion(
#                         title=item.get("title", ""),
#                         link=item.get("link", ""),
#                         snippet=item.get("snippet", "")
#                     )
#                 )
        
#         return schemas.SuggestionResponse(query=query, suggestions=suggestions)