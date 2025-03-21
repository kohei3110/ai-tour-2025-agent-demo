import os
import pytest
import json
from unittest.mock import Mock, patch, mock_open, PropertyMock
from json.decoder import JSONDecodeError
from azure.ai.projects.models import RunStatus, MessageRole, MessageTextContent
from services.assistant_manager_service import AssistantManagerService
from models.models import MessageRequest


@pytest.fixture
def mock_project_client():
    """AIProjectClientのモックを作成するフィクスチャ"""
    client = Mock()
    
    # エージェント作成のモック
    agent = Mock()
    agent.id = "test-agent-id"
    client.agents.create_agent.return_value = agent
    
    # スレッド作成のモック
    thread = Mock()
    thread.id = "test-thread-id"
    client.agents.create_thread.return_value = thread
    
    # メッセージ作成のモック
    client.agents.create_message.return_value = None
    
    return client


@pytest.fixture
def service(mock_project_client):
    """AssistantManagerServiceのインスタンスを作成するフィクスチャ"""
    return AssistantManagerService(mock_project_client)


@pytest.fixture
def valid_openapi_spec():
    """有効なOpenAPIスペックを返すフィクスチャ"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Subsidies API",
            "version": "1.0.0"
        },
        "paths": {
            "/subsidies": {
                "get": {
                    "summary": "Get all subsidies",
                    "responses": {
                        "200": {
                            "description": "Successful response"
                        }
                    }
                }
            }
        }
    }


class TestAssistantManagerService:
    
    # TS-002: OpenAPIスペックファイル不在テスト
    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_load_openapi_spec_file_not_found(self, mock_open_file, service):
        """スペックファイルが存在しない場合のload_openapi_specメソッドの挙動をテスト"""
        with pytest.raises(FileNotFoundError):
            service.load_openapi_spec()
    
    # TS-003: 無効なOpenAPIスペックテスト
    @patch("builtins.open", mock_open(read_data="invalid json"))
    @patch("jsonref.loads", side_effect=JSONDecodeError("Invalid JSON", "invalid json", 0))
    def test_load_openapi_spec_invalid_json(self, mock_loads, service):
        """無効な形式のOpenAPIスペックファイルの場合のload_openapi_specメソッドの挙動をテスト"""
        with pytest.raises(JSONDecodeError):
            service.load_openapi_spec()
    
    # TS-004: OpenAPIツール作成テスト
    @patch("services.assistant_manager_service.swagger_spec_tool.create_subsidies_tool")
    def test_create_openapi_tool(self, mock_create_tool, service, valid_openapi_spec):
        """create_openapi_toolメソッドが正常にツールを作成できることをテスト"""
        # モックの戻り値を設定
        mock_tool = Mock()
        mock_create_tool.return_value = mock_tool
        
        # メソッド実行
        result = service.create_openapi_tool(valid_openapi_spec)
        
        # 検証
        mock_create_tool.assert_called_once_with(valid_openapi_spec)
        assert result == mock_tool
    
    # TS-005: メッセージ処理成功テスト
    @pytest.mark.asyncio
    @patch.object(AssistantManagerService, "load_openapi_spec")
    @patch.object(AssistantManagerService, "create_openapi_tool")
    async def test_process_openapi_spec_success(self, mock_create_tool, mock_load_spec, service, mock_project_client):
        """process_openapi_specメソッドが正常にメッセージを処理できることをテスト"""
        # モックの設定
        mock_load_spec.return_value = {"spec": "value"}
        mock_tool = Mock()
        mock_tool.definitions = [{"type": "openapi"}]
        mock_create_tool.return_value = mock_tool
        
        # 実行成功のモック
        run = Mock()
        # Azure SDKのRunStatusの正しい値を使用
        type(run).status = PropertyMock(side_effect=lambda: RunStatus.FAILED.__class__("completed"))
        mock_project_client.agents.create_and_process_run.return_value = run
        
        # メッセージリストのモック
        message = Mock()
        message.role = MessageRole.AGENT
        message_content = Mock(spec=MessageTextContent)
        message_content.text.value = "This is a test response"
        message.content = [message_content]
        messages = Mock()
        messages.data = [message]
        mock_project_client.agents.list_messages.return_value = messages
        
        # リクエスト作成
        request = MessageRequest(message="Test message")
        
        # メソッド実行 - 非同期なのでawaitする
        result = await service.process_openapi_spec(request)
        
        # 検証
        assert result == {"response": "This is a test response"}
        mock_project_client.agents.delete_agent.assert_called_once()
    
    # TS-006: エージェント実行失敗テスト
    @pytest.mark.asyncio
    @patch.object(AssistantManagerService, "load_openapi_spec")
    @patch.object(AssistantManagerService, "create_openapi_tool")
    async def test_process_openapi_spec_run_failed(self, mock_create_tool, mock_load_spec, service, mock_project_client):
        """エージェント実行が失敗した場合のprocess_openapi_specメソッドの挙動をテスト"""
        # モックの設定
        mock_load_spec.return_value = {"spec": "value"}
        mock_tool = Mock()
        mock_tool.definitions = [{"type": "openapi"}]
        mock_create_tool.return_value = mock_tool
        
        # 実行失敗のモック
        run = Mock()
        # PropertyMockを使用してstatusプロパティを正しくモック
        status_property = PropertyMock(return_value=RunStatus.FAILED)
        type(run).status = status_property
        run.last_error = "Test error"
        mock_project_client.agents.create_and_process_run.return_value = run
        
        # リクエスト作成
        request = MessageRequest(message="Test message")
        
        # メソッド実行 - 非同期なのでawaitする
        result = await service.process_openapi_spec(request)
        
        # 検証
        assert result == {"error": f"Run failed: {run.last_error}"}
        mock_project_client.agents.delete_agent.assert_called_once()
    
    # TS-007: 予期しない例外処理テスト
    @pytest.mark.asyncio
    @patch.object(AssistantManagerService, "load_openapi_spec", side_effect=Exception("Unexpected error"))
    async def test_process_openapi_spec_unexpected_exception(self, mock_load_spec, service):
        """予期しない例外が発生した場合のprocess_openapi_specメソッドの挙動をテスト"""
        # リクエスト作成
        request = MessageRequest(message="Test message")
        
        # メソッド実行 - 非同期なのでawaitする
        result = await service.process_openapi_spec(request)
        
        # 検証
        assert result == {"error": "Error processing request: Unexpected error"}
    
    # TS-008: エージェント応答なしテスト
    @pytest.mark.asyncio
    @patch.object(AssistantManagerService, "load_openapi_spec")
    @patch.object(AssistantManagerService, "create_openapi_tool")
    async def test_process_openapi_spec_no_response(self, mock_create_tool, mock_load_spec, service, mock_project_client):
        """エージェントから応答がない場合のprocess_openapi_specメソッドの挙動をテスト"""
        # モックの設定
        mock_load_spec.return_value = {"spec": "value"}
        mock_tool = Mock()
        mock_tool.definitions = [{"type": "openapi"}]
        mock_create_tool.return_value = mock_tool
        
        # 実行成功のモック
        run = Mock()
        # Azure SDKのRunStatusの正しい値を使用
        type(run).status = PropertyMock(side_effect=lambda: RunStatus.FAILED.__class__("completed"))
        mock_project_client.agents.create_and_process_run.return_value = run
        
        # 空のメッセージリストのモック
        messages = Mock()
        messages.data = []
        mock_project_client.agents.list_messages.return_value = messages
        
        # リクエスト作成
        request = MessageRequest(message="Test message")
        
        # メソッド実行 - 非同期なのでawaitする
        result = await service.process_openapi_spec(request)
        
        # 検証
        assert result == {"response": "No response found"}
        mock_project_client.agents.delete_agent.assert_called_once()