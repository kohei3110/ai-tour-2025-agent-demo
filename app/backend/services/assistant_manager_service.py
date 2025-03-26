"""
AI アシスタントマネージャーサービス
"""

import json
import logging
from typing import Dict, Any, Optional
from azure.ai.projects import AIProjectClient
from tools.common_utils import generate_application_text
from models.models import MessageRequest

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

    async def process_openapi_spec(self, request: MessageRequest) -> Dict[str, str]:
        """
        OpenAPIスペックを処理し、応答を生成する
        
        Args:
            request: ユーザーからのメッセージリクエスト
            
        Returns:
            生成された応答を含む辞書
        """
        try:
            # OpenAPIスペックの読み込み
            spec_path = "tools/actions/specs/swagger_subsidies.json"
            spec = self.load_openapi_spec(spec_path)
            
            # OpenAPIツールの作成
            openapi_tool = self.create_openapi_tool(spec)
            
            # エージェントがなければ作成
            if not self._agent_id:
                # エージェントの作成（OpenAPIツールを追加）
                agent = self.project_client.agents.create_agent(
                    name="補助金情報案内AIエージェント",
                    instructions="""あなたは補助金申請のエキスパートアシスタントです。
ユーザーからの質問に対して、OpenAPIツールを使用して補助金情報を検索し、
わかりやすく回答してください。""",
                    description="補助金情報案内AIエージェント",
                    tools=[openapi_tool]  # ツールを追加
                )
                self._agent_id = agent.id

            # スレッドの作成
            thread = self.project_client.agents.create_thread()
            
            # メッセージの作成
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=request.message
            )
            
            # エージェントの実行
            run = self.project_client.agents.create_and_process_run(
                agent_id=self._agent_id,
                thread_id=thread.id
            )
            
            # エラー発生時の処理
            if run.status != "completed" or run.last_error:
                logger.error(f"Agent execution failed: {run.last_error}")
                return {"error": f"Run failed: {run.last_error}"}
            
            # レスポンスの取得
            responses = self.project_client.agents.list_messages(thread_id=thread.id)
            for response in responses.data:
                if response.role == "assistant":
                    for content in response.content:
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            try:
                                # 応答を取得
                                response_text = content.text.value
                                
                                # JSON化できない複雑なオブジェクトは文字列に変換
                                # isinstance(response_text, object)は全てのオブジェクトにマッチするため、
                                # 基本型は個別に除外する必要がある
                                if not isinstance(response_text, (str, int, float, bool, list, dict, type(None))):
                                    response_text = str(response_text)
                                
                                # 辞書や配列内の非シリアライズ可能なオブジェクトも処理
                                if isinstance(response_text, dict):
                                    response_text = self._ensure_serializable_dict(response_text)
                                elif isinstance(response_text, list):
                                    response_text = self._ensure_serializable_list(response_text)
                                    
                                return {"response": response_text}
                            except TypeError as e:
                                # JSONシリアライズエラー
                                logger.error(f"JSON serialization error: {str(e)}")
                                # エラーメッセージを返す代わりに、応答テキストを文字列化して返す
                                return {"response": f"Response received but could not be fully serialized: {str(content.text.value)}"}
            
            return {"response": "No response found"}
            
        except Exception as e:
            logger.error(f"Failed to process OpenAPI spec: {str(e)}")
            return {"error": f"Error processing request: {str(e)}"}

    def _ensure_serializable_dict(self, data: dict) -> dict:
        """辞書内の非シリアライズ可能なオブジェクトを文字列に変換する

        Args:
            data: 変換対象の辞書

        Returns:
            JSON シリアライズ可能な辞書
        """
        result = {}
        for key, value in data.items():
            # キーが文字列でない場合は文字列に変換
            if not isinstance(key, str):
                key = str(key)
                
            # 値を再帰的に処理
            if isinstance(value, dict):
                result[key] = self._ensure_serializable_dict(value)
            elif isinstance(value, list):
                result[key] = self._ensure_serializable_list(value)
            elif not isinstance(value, (str, int, float, bool, type(None))):
                # 基本型以外は文字列に変換
                result[key] = str(value)
            else:
                result[key] = value
        return result
    
    def _ensure_serializable_list(self, data: list) -> list:
        """リスト内の非シリアライズ可能なオブジェクトを文字列に変換する

        Args:
            data: 変換対象のリスト

        Returns:
            JSON シリアライズ可能なリスト
        """
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(self._ensure_serializable_dict(item))
            elif isinstance(item, list):
                result.append(self._ensure_serializable_list(item))
            elif not isinstance(item, (str, int, float, bool, type(None))):
                # 基本型以外は文字列に変換
                result.append(str(item))
            else:
                result.append(item)
        return result
        
    def process_message(self, prompt: str) -> str:
        """
        一般的なメッセージ処理の実装
        
        Args:
            prompt: ユーザーからのプロンプト
            
        Returns:
            生成された応答
        """
        try:
            # 一時的なエージェントの作成
            agent = self.project_client.agents.create_agent(
                name="テキスト生成エージェント",
                instructions=f"ユーザーのプロンプトに対して適切なテキストを生成してください。",
                description="テキスト生成エージェント"
            )
            
            try:
                # スレッドの作成
                thread = self.project_client.agents.create_thread()
                
                # メッセージの作成
                self.project_client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=prompt
                )
                
                # エージェントの実行
                run = self.project_client.agents.create_and_process_run(
                    agent_id=agent.id,
                    thread_id=thread.id
                )
                
                # エラー発生時の処理
                if run.status != "completed" or run.last_error:
                    return f"Error: {run.last_error}"
                
                # レスポンスの取得
                responses = self.project_client.agents.list_messages(thread_id=thread.id)
                for response in responses.data:
                    if response.role == "assistant":
                        for content in response.content:
                            if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                return content.text.value
                
                return "No response found"
                
            finally:
                # エージェントの削除
                self.project_client.agents.delete_agent(agent.id)
                
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            return f"Error processing request: {str(e)}"