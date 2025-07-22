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

# class SuggestionService:
#     @staticmethod
#     def _create_tavily_query(req: schemas.SuggestionRequest) -> str:
#         """ユーザーの状況からTavily検索用のクエリを生成する"""
#         duration_hours = (req.free_time_end - req.free_time_start).total_seconds() / 3600
        
#         # 場所の情報を優先
#         locations = []
#         if req.prev_event and req.prev_event.location:
#             locations.append(req.prev_event.location)
#         # 前後の場所が違う場合のみ追加
#         if req.next_event and req.next_event.location:
#             if not locations or locations[0] != req.next_event.location:
#                 locations.append(req.next_event.location)

#         if locations:
#             return f"{'または'.join(locations)}周辺で{duration_hours:.1f}時間で楽しめること"
        
#         return "近くで短時間で楽しめるアクティビティ"

#     @staticmethod
#     def _create_openai_prompt(req: schemas.SuggestionRequest, tavily_context: str) -> str:
#         """Tavilyの検索結果を元に、OpenAIへの詳細な指示プロンプトを生成する"""
        
#         # 状況説明
#         situation = f"""
#         # ユーザーの状況
#         - 直前の予定: {req.prev_event.content if req.prev_event else 'なし'}
#         - 直前の予定の場所: {req.prev_event.location if req.prev_event else '不明'}
#         - 空き時間の開始: {req.free_time_start.strftime('%H:%M')}
#         - 空き時間の終了: {req.free_time_end.strftime('%H:%M')}
#         - 直後の予定: {req.next_event.content if req.next_event else 'なし'}
#         - 直後の予定の場所: {req.next_event.location if req.next_event else '不明'}

#         # Web検索から得られた参考情報
#         {tavily_context}
#         """

#         # 指示
#         instruction = f"""
#         # あなたのタスク
#         あなたは非常に優秀な旅行プランナーです。上記の「ユーザーの状況」と「参考情報」を元に、空き時間を最大限に活用できる、具体的で実行可能なプランを1つ提案してください。
#         以下の制約条件と出力形式を厳守してください。

#         # 制約条件
#         - 提案するアクティビティの開始から終了、そして次の予定への移動時間まで、すべてがユーザーの空き時間内に収まるように計画してください。
#         - 移動時間は現実的な値を想定してください（例：徒歩10分、電車15分など）。
#         - 提案する内容は、参考情報に基づいた、事実ベースのものにしてください。

#         # 出力形式 (必ずこのJSON形式で出力してください)
#         {{
#           "title": "提案アクティビティの魅力的なタイトル",
#           "description": "なぜこのプランがおすすめなのか、具体的な説明",
#           "activity_start_time": "{req.free_time_start.strftime('%Y-%m-%dT%H:%M:%S')}",
#           "activity_end_time": "{req.free_time_end.strftime('%Y-%m-%dT%H:%M:%S')}",
#           "location": "アクティビティを行う具体的な場所",
#           "estimated_cost": "おおよその費用（例：1,500円, 無料）",
#           "travel_from_previous": {{
#             "mode": "移動手段（徒歩、電車、バス、タクシーなど）",
#             "duration_minutes": 15,
#             "instructions": "前の予定の場所からの具体的な移動指示"
#           }},
#           "travel_to_next": {{
#             "mode": "移動手段",
#             "duration_minutes": 20,
#             "instructions": "提案場所から次の予定の場所への具体的な移動指示"
#           }},
#           "source_link": "参考にした情報のURL"
#         }}
#         """
#         return situation + instruction

#     @staticmethod
#     async def get_suggestions(req: schemas.SuggestionRequest) -> schemas.SuggestionResponse:
#         if not openai_client.api_key or not tavily_client.api_key:
#             raise ValueError("API Key is not set.")

#         # 1. Tavilyで検索クエリを生成し、情報を検索
#         tavily_query = SuggestionService._create_tavily_query(req)
#         try:
#             search_result = tavily_client.search(
#                 query=tavily_query,
#                 search_depth="advanced", # より詳細な検索
#                 max_results=5
#             )
#             # 検索結果を文脈として整形
#             tavily_context = "\n".join([f"- {res['content']} (Source: {res['url']})" for res in search_result['results']])
#         except Exception as e:
#             raise ConnectionError(f"Tavily API search failed: {e}")

#         # 2. OpenAIに渡すプロンプトを生成
#         openai_prompt = SuggestionService._create_openai_prompt(req, tavily_context)

#         # 3. OpenAI APIを呼び出し、詳細なプランを生成させる
#         try:
#             response = await openai_client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[{"role": "system", "content": openai_prompt}],
#                 temperature=0.5,
#                 response_format={"type": "json_object"}
#             )
#             content = response.choices[0].message.content
#             if not content:
#                 raise ValueError("OpenAI API returned an empty response.")
            
#             # JSONをパースし、Pydanticモデルに変換
#             plan_data = json.loads(content)
#             suggestion = schemas.Suggestion(**plan_data)
            
#             return schemas.SuggestionResponse(
#                 search_query=tavily_query,
#                 suggestions=[suggestion] # 1つの詳細なプランを返す
#             )
#         except Exception as e:
#             raise ConnectionError(f"OpenAI API call failed: {e}")

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
        
        
# 今多分このエージェントと上のmobilityエージェントしか使ってない状態のはず。(村重)
class MasterPlannerAgent:
    @staticmethod
    def _create_tavily_query_for_plans(req: schemas.MobilityRequest, mobility_decision: schemas.MobilityResponse) -> str:
        """プラン生成のために、移動判断に基づいた検索クエリを作成する"""
        
        # 移動に使える合計時間から、推奨移動モードでの移動時間を引いた時間が、純粋な活動時間
        net_activity_minutes = ((req.next_event_start_time - req.prev_event_end_time).total_seconds() / 60) - mobility_decision.estimated_time
        
        if net_activity_minutes < 15: # 活動時間が短すぎる場合
             return f"{req.prev_event_location}で15分以内にできること"

        if mobility_decision.use_public_transport:
            # 公共交通機関を使う場合、出発地・目的地・またはその沿線で探す
            return f"{req.prev_event_location}から{req.next_event_location}の間、またはその周辺で{net_activity_minutes:.0f}分で楽しめること"
        else:
            # 徒歩などの場合、出発地のすぐ近くで探す
            return f"{req.prev_event_location}周辺で{net_activity_minutes:.0f}分で楽しめること"

    @staticmethod
    def _create_final_planning_prompt(
        req: schemas.MobilityRequest,
        mobility_decision: schemas.MobilityResponse,
        search_context: str
    ) -> str:
        prompt = f"""
        あなたは、ユーザーの状況を深く理解し、最高の体験を提案するエキスパート・プランナーです。
        以下のすべての情報を分析し、ユーザーに2つの異なる魅力的な行動プランを提案してください。
        各プランは、移動やアクティビティを含む一連の「イベントの集合」として構成してください。

        # ユーザーの基本情報
        - 出発地: {req.prev_event_location}
        - 前の予定の終了時刻: {req.prev_event_end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        - 目的地: {req.next_event_location}
        - 次の予定の開始時刻: {req.next_event_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        - ユーザーの好み: 「{req.user_preferences}」

        # あなたが行った移動判断
        {mobility_decision.reasoning}
        推奨する移動手段は「{mobility_decision.recommended_mode}」で、所要時間は約{mobility_decision.estimated_time}分です。

        # Web検索から得られた参考情報
        {search_context}

        # あなたの最終タスク
        上記の情報を基に、ユーザーの好みを満たす、創造的で具体的な行動プランを2パターン生成してください。
        各プランは、以下の要素からなるイベントのリストで構成されます。
        1. 【移動】前の予定の場所からアクティビティの場所への移動
        2. 【アクティビティ】メインの活動
        3. 【移動】アクティビティの場所から次の予定の場所への移動

        時間計算は厳密に行ってください。前の予定の終了から次の予定の開始まですべての時間が埋まるように、イベントのstart_timeとend_timeを正確に設定してください。
        必ず、以下のJSON形式で、2つのプランのリストとして出力してください。

        {{
          "plans": [
            {{
              "pattern_description": "プラン1のテーマ（例：静かなカフェで読書プラン）",
              "events": [
                {{
                  "title": "移動：{req.prev_event_location}からアクティビティ場所へ",
                  "start_time": "{req.prev_event_end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                  "end_time": "...",
                  "location": "{req.prev_event_location}",
                  "description": "移動手段：{mobility_decision.recommended_mode}"
                }},
                {{
                  "title": "アクティビティのタイトル",
                  "start_time": "...",
                  "end_time": "...",
                  "location": "アクティビティの具体的な場所",
                  "description": "アクティビティの具体的な内容"
                }},
                {{
                  "title": "移動：アクティビティ場所から{req.next_event_location}へ",
                  "start_time": "...",
                  "end_time": "{req.next_event_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                  "location": "アクティビティの場所",
                  "description": "移動手段：..."
                }}
              ]
            }},
            {{
              "pattern_description": "プラン2のテーマ（例：話題の雑貨屋巡りプラン）",
              "events": [
                {{
                  "title": "移動：...",
                  "start_time": "...",
                  "end_time": "...",
                  "location": "...",
                  "description": "..."
                }},
                {{
                  "title": "...",
                  "start_time": "...",
                  "end_time": "...",
                  "location": "...",
                  "description": "..."
                }},
                {{
                  "title": "移動：...",
                  "start_time": "...",
                  "end_time": "...",
                  "location": "...",
                  "description": "..."
                }}
              ]
            }}
          ]
        }}
        """
        return prompt

    @staticmethod
    async def generate_plans(req: schemas.MobilityRequest) -> schemas.PlannerResponse:
        # 1. まず移動手段を決定する
        mobility_decision = await MobilityAgent.decide_mobility(req)

        # 2. 移動判断に基づき、プランのアイデアをWeb検索する
        tavily_query = MasterPlannerAgent._create_tavily_query_for_plans(req, mobility_decision)
        search_result = tavily_client.search(query=tavily_query, search_depth="advanced", max_results=7)
        search_context = "\n".join([f"- {res['content']}" for res in search_result['results']])

        # 3. 全ての情報を統合し、最終的なプラン生成をAIに指示する
        final_prompt = MasterPlannerAgent._create_final_planning_prompt(req, mobility_decision, search_context)
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": final_prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("AI Planner returned an empty response.")
        
        plans_data = json.loads(content)
        
        # 新しいPlanPatternスキーマを使ってレスポンスを構築する
        return schemas.PlannerResponse(
            mobility_decision=mobility_decision,
            plans=[schemas.PlanPattern(**plan) for plan in plans_data.get('plans', [])]
        )

# app/services.py に以下の新しいクラスを追記

class MasculineAgent:
    @staticmethod
    def _create_tavily_query(req: schemas.MobilityRequest) -> str:
        """トライアスリート向けのトレーニング場所を検索するクエリを生成する"""
        
        # available_minutes = (req.next_event_start_time - req.prev_event_end_time).total_seconds() / 60
        origin = req.prev_event_location
        destination = req.next_event_location

        # クエリをより具体的に
        return f"{origin}と{destination}の間にある、またはその周辺の、ランニングコース、オープンウォータースイミングができる場所、登山・トレイルランニングができる山。ジムや公共のトレーニング施設も含む。体を鍛えることができる場所であれば基本的にどこでも良い。"

    @staticmethod
    def _create_final_planning_prompt(req: schemas.MobilityRequest, search_context: str) -> str:
        """超ストイックなトレーニングプランの生成を指示する最終プロンプトを作成する"""
        
        prompt = f"""
        あなたは、トライアスロン世界大会優勝を目指すアスリートを指導する、鬼コーチです。
        これから、選手の空き時間を使った、極限まで追い込むトレーニングプランを2つ立案してください。

        # 選手の状況
        - 前の予定の終了時刻: {req.prev_event_end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        - 出発地: {req.prev_event_location}
        - 次の予定の開始時刻: {req.next_event_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        - 目的地: {req.next_event_location}
        - 選手の好み・目標: 「{req.user_preferences}」

        # Web検索から得られたトレーニング場所の情報
        {search_context}

        # 絶対厳守のルール
        - 移動手段は「走る」「泳ぐ」「山を登る」のいずれか、またはその組み合わせのみとする。絶対に他の移動手段を提案してはならない。
        - 2地点間の距離が多少遠くても、上記の手段で移動するものとする。
        - ただし、移動時間は厳密に計算し、前の予定の終了から次の予定の開始までの時間内に収めること。
        - 上記の手段での移動により、時間内に移動できない場合は、電車やバスなどの公共交通機関を使うことは許可するが、あくまで例外的な措置とする。
        - プランは常にトレーニングであること。休憩や観光の要素は一切不要。
        - 時間計算は厳密に行い、前の予定の終了から次の予定の開始まで、1分たりとも無駄にしないこと。

        # あなたの最終タスク
        上記の全てを考慮し、最も過酷で効果的なトレーニングプランを2パターン生成してください。
        必ず、以下のJSON形式で、2つのプランのリストとして出力してください。

        {{
          "plans": [
            {{
              "pattern_description": "プラン1のテーマ（例：心肺機能を追い込む峠走プラン）",
              "events": [
                {{
                  "title": "移動(RUN): {req.prev_event_location}からトレーニング場所へ",
                  "start_time": "...", "end_time": "...", "location": "...", "description": "全力で走る。ペースはキロ4分を目指す。"
                }},
                {{
                  "title": "トレーニング: （例）〇〇山 ヒルクライムインターバル",
                  "start_time": "...", "end_time": "...", "location": "...", "description": "..."
                }},
                {{
                  "title": "移動(RUN): トレーニング場所から{req.next_event_location}へ",
                  "start_time": "...", "end_time": "...", "location": "...", "description": "クールダウンを兼ねてジョグで移動。"
                }}
              ]
            }},
            {{
              "pattern_description": "プラン2のテーマ（例：実戦想定ブリックトレーニング）",
              "events": [ ... ]
            }}
          ]
        }}
        """
        return prompt

    @staticmethod
    async def generate_plans(req: schemas.MobilityRequest) -> schemas.PlannerResponse:
        """MasculineAgentのメイン処理"""
        
        # 1. トレーニング場所のアイデアをWeb検索
        tavily_query = MasculineAgent._create_tavily_query(req)
        search_result = tavily_client.search(query=tavily_query, search_depth="advanced", max_results=7)
        search_context = "\n".join([f"- {res['content']}" for res in search_result['results']])

        # 2. 最終的なプラン生成をAIに指示
        final_prompt = MasculineAgent._create_final_planning_prompt(req, search_context)
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": final_prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("AI Planner returned an empty response.")
        
        plans_data = json.loads(content)
        
        # MobilityAgentを使わないので、ダミーの判断結果を生成してレスポンスの型を合わせる
        dummy_mobility_decision = schemas.MobilityResponse(
            use_public_transport=False,
            recommended_mode="己の肉体",
            reasoning="アスリートに文明の利器は不要。移動は全てトレーニングの一環である。",
            estimated_time=0, # 時間はプラン内で計算
            estimated_cost="0円"
        )
        
        return schemas.PlannerResponse(
            mobility_decision=dummy_mobility_decision,
            plans=[schemas.PlanPattern(**plan) for plan in plans_data.get('plans', [])]
        )