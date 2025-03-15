from fastapi import APIRouter, Depends

from models.models import MessageRequest
from services.assistant_manager_service import AssistantManagerService
from startup import assistant_manager_service


router = APIRouter()



@router.get("/health")
def get_health():
    """
    ヘルスチェックエンドポイント。

    Returns:
        dict: アプリケーションのステータスを含む辞書。
    """
    return {"status": "ok"}


@router.post("/api/chat")
def post_assistant_manager_service(
    request: MessageRequest, 
    assistant_manager_service: AssistantManagerService = Depends(lambda: assistant_manager_service)
):
    """
    エージェントに対してプロンプトを送信するエンドポイント。

    Args:
        request (MessageRequest): メッセージリクエスト。
    
    Returns:
        dict: エージェントの応答を含む辞書。
    """
    user_message = request.message
    response = assistant_manager_service.send_prompt(user_message)
    
    # レスポンス形式をそのまま返す
    # response には {"response": assistant_messages, "sources": url_citations} が含まれる
    return response