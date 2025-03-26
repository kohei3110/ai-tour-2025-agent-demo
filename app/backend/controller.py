from fastapi import APIRouter, Depends, HTTPException
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from typing import Literal, Dict, Any, Optional
from models.models import MessageRequest, ApplicationFormRequest, PromptRequest
from services.assistant_manager_service import AssistantManagerService
from tools.actions.application_doc_generator_tool import ApplicationFormGenerator
from startup import assistant_manager_service
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

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

@router.post("/api/application/generate")
async def generate_application_form(request: ApplicationFormRequest):
    """
    補助金申請書テンプレートを生成するエンドポイント。
    AIを使用してリクエストの補助金情報に基づいたテンプレートを生成します。
    
    Args:
        request (ApplicationFormRequest): 補助金情報とビジネス概要を含むリクエスト
    
    Returns:
        dict: 生成された申請書テンプレートを含む辞書
    """
    try:
        # 補助金情報が空の場合はエラー
        if not request.subsidy_info:
            raise HTTPException(status_code=400, detail="補助金情報が必要です")
        
        # ApplicationFormGeneratorのインスタンスを作成
        form_generator = ApplicationFormGenerator()
        
        # ビジネス概要が提供されている場合はAI拡張テンプレートを生成
        if request.business_description:
            application_text = await form_generator.generate_ai_enhanced(
                request.subsidy_info, 
                request.business_description
            )
        # ビジネス概要がない場合は基本テンプレートのみを生成
        else:
            application_text = form_generator.generate(request.subsidy_info)
        
        return {
            "template": application_text,
            "ai_enhanced": bool(request.business_description)
        }
        
    except Exception as e:
        logger.error(f"申請書テンプレート生成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"申請書テンプレート生成中にエラーが発生しました: {str(e)}")

@router.post("/api/generate")
async def generate_message(
    request: PromptRequest,
    assistant_manager_service: AssistantManagerService = Depends(lambda: assistant_manager_service)
):
    """
    AIにプロンプトを送信してメッセージを生成するエンドポイント。
    
    Args:
        request (PromptRequest): プロンプトを含むリクエスト
    
    Returns:
        dict: 生成されたメッセージを含む辞書
    """
    try:
        # プロンプトが空の場合はエラー
        if not request.prompt:
            raise HTTPException(status_code=400, detail="プロンプトが必要です")
        
        # AssistantManagerServiceのprocess_messageメソッドを呼び出す
        generated_text = assistant_manager_service.process_message(request.prompt)
        
        return {
            "generated_text": generated_text,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"メッセージ生成エラー: {str(e)}")
        return {
            "generated_text": f"メッセージ生成中にエラーが発生しました: {str(e)}",
            "success": False
        }