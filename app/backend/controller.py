from fastapi import APIRouter, Depends
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from typing import Literal

from models.models import MessageRequest
from services.assistant_manager_service import AssistantManagerService
from startup import assistant_manager_service


router = APIRouter()


@router.get("/api/health")
def get_health():
    """
    ヘルスチェックエンドポイント。

    Returns:
        dict: アプリケーションのステータスを含む辞書。
    """
    return {"status": "ok"}


@router.post("/api/chat")
async def post_assistant_manager_service(
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
    return await assistant_manager_service.process_openapi_spec(request)