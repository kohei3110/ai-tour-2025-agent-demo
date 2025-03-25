"""
AI アシスタントマネージャーサービス
"""

import json
import logging
from typing import Dict, Any, Optional
from azure.ai.projects import AIProjectClient
from tools.common_utils import generate_application_text

# ロガーの設定
logger = logging.getLogger(__name__)

class AssistantManagerService:
    """AI アシスタントマネージャーサービス"""

    def __init__(self, project_client: AIProjectClient):
        """
        初期化
        
        Args:
            project_client: Azure AIプロジェクトクライアント
        """
        self.project_client = project_client
        self._agent_id = None

    def load_openapi_spec(self, file_path: str) -> Dict[str, Any]:
        """
        OpenAPIスペックファイルを読み込む
        
        Args:
            file_path: スペックファイルのパス
            
        Returns:
            OpenAPIスペック辞書
            
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            json.JSONDecodeError: JSONパースエラー
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"OpenAPI specification file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAPI specification: {str(e)}")
            raise

    def create_openapi_tool(self, spec: Dict[str, Any]) -> Any:
        """
        OpenAPIツールを作成する
        
        Args:
            spec: OpenAPIスペック辞書
            
        Returns:
            作成されたOpenAPIツール
        """
        try:
            from tools.actions.swagger_spec_tool import create_subsidies_tool
            return create_subsidies_tool(spec)
        except Exception as e:
            logger.error(f"Failed to create OpenAPI tool: {str(e)}")
            raise

    def process_openapi_spec(self, message: str) -> str:
        """
        OpenAPIスペックを処理し、応答を生成する
        
        Args:
            message: ユーザーからのメッセージ
            
        Returns:
            生成された応答
        """
        try:
            # エージェントがなければ作成
            if not self._agent_id:
                # エージェントの作成
                agent = self.project_client.agents.create_agent(
                    name="補助金情報案内AIエージェント",
                    instructions="""あなたは補助金申請のエキスパートアシスタントです。
ユーザーからの質問に対して、OpenAPIツールを使用して補助金情報を検索し、
わかりやすく回答してください。""",
                    description="補助金情報案内AIエージェント"
                )
                self._agent_id = agent.id

            # スレッドの作成
            thread = self.project_client.agents.create_thread()
            
            # メッセージの作成
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=message
            )
            
            # エージェントの実行
            run = self.project_client.agents.create_and_process_run(
                agent_id=self._agent_id,
                thread_id=thread.id
            )
            
            # エラー発生時の処理
            if run.last_error:
                logger.error(f"Agent execution failed: {run.last_error}")
                return f"エージェントの実行に失敗しました: {run.last_error}"
            
            # レスポンスの取得
            responses = self.project_client.agents.list_messages(thread_id=thread.id)
            for response in responses:
                if response.role == "assistant":
                    return response.content
            
            return "No response found"
            
        except Exception as e:
            logger.error(f"Failed to process OpenAPI spec: {str(e)}")
            return f"エラーが発生しました: {str(e)}"