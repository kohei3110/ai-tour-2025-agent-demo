from fastapi import APIRouter, Depends
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

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
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    user_message = request.message
    az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4o-mini",
        api_version="2024-10-21",
        model = "gpt-4o-mini",
        azure_endpoint="https://agent-ai-serviceslbiu.openai.azure.com/",
        azure_ad_token_provider=token_provider
    )
    bing_search_agent = AssistantAgent(
        name="bing_search_agent",
        model_client=az_model_client,
        tools=[assistant_manager_service.web_ai_agent],
        system_message="You are a search expert, help me use tools to find relevant knowledge",
    )
    subsides_agent = AssistantAgent(
        name="subsidies_agent",
        model_client=az_model_client,
        tools=[assistant_manager_service.subsidies_agent],
        system_message="You are a subsidies expert, help me use tools to find relevant knowledge",
    )
    reflection_team = RoundRobinGroupChat(
        [bing_search_agent, subsides_agent],
        max_turns=3,
    )
    return reflection_team.run(user_message)