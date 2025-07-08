import os
import logging
from typing import TypedDict, List, Optional, cast
from tavily import TavilyClient

logger = logging.getLogger(__name__)

class SearchResult(TypedDict):
    url: str
    title: str
    content: str
    score: float
    raw_content: Optional[str]

class SearchResponse(TypedDict):
    query: str
    follow_up_questions: Optional[str]
    answer: Optional[str]
    images: List[str]
    results: List[SearchResult]
    response_time: float

class SearchError(Exception):
    """検索関連のエラー"""
    pass

def search(query: str, limit: int = 5) -> SearchResponse:
    """
    Web検索を実行する
    
    Args:
        query: 検索クエリ
        limit: 結果の最大数（デフォルト: 5）
    
    Returns:
        SearchResponse: 検索結果
    
    Raises:
        SearchError: 検索実行時のエラー
        ValueError: 無効な入力パラメータ
    """
    # 入力検証
    if not query or not query.strip():
        raise ValueError("検索クエリは空文字列にできません")
    
    if limit <= 0 or limit > 50:
        raise ValueError("limitは1-100の範囲で指定してください")
    
    # API キーの検証
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise SearchError("TAVILY_API_KEYが設定されていません")
    
    try:
        client = TavilyClient(api_key)
        response = client.search(query.strip(), limit=limit)
        
        # レスポンス構造の基本的な検証
        if not isinstance(response, dict):
            raise SearchError("APIレスポンスの形式が不正です")
        
        # 必須フィールドの存在確認
        required_fields = ['query', 'results']
        for field in required_fields:
            if field not in response:
                logger.warning(f"レスポンスに必須フィールド '{field}' がありません")
        
        return cast(SearchResponse, response)
        
    except Exception as e:
        logger.error(f"検索API エラー: {e}")
        raise SearchError(f"検索中にエラーが発生しました: {e}")

def is_search_available() -> bool:
    """
    検索機能が利用可能かチェック
    
    Returns:
        bool: 検索機能が利用可能な場合True
    """
    return bool(os.getenv("TAVILY_API_KEY"))
