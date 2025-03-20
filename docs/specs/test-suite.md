# 単体テストケース一覧

このドキュメントはAI Tour 2025 Agent Demoアプリケーションのための単体テストケース一覧を提供します。テスト駆動開発（TDD）の原則に従い、これらのテストケースは実装前に作成し、コードの品質と機能の正確性を保証するために使用します。

## 1. モデル層テスト

### 1.1 MessageRequest モデル

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TM-001 | 有効なメッセージリクエスト作成テスト | 有効なメッセージを含むMessageRequestオブジェクトの作成をテスト | オブジェクトが正常に作成される |
| TM-002 | 空のメッセージリクエスト作成テスト | 空のメッセージを含むMessageRequestオブジェクトの作成をテスト | バリデーションエラーが発生する |
| TM-003 | 非常に長いメッセージリクエスト作成テスト | 非常に長いメッセージを含むMessageRequestオブジェクトの作成をテスト | オブジェクトが正常に作成される |

## 2. コントローラー層テスト

### 2.1 ヘルスチェックエンドポイント

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TC-001 | ヘルスチェックエンドポイント正常応答テスト | `/api/health` エンドポイントへのGETリクエストをテスト | ステータスコード200と `{"status": "ok"}` の応答が返される |

### 2.2 チャットエンドポイント

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TC-002 | 有効なメッセージ送信テスト | 有効なメッセージを `/api/chat` エンドポイントに送信 | 正常なレスポンスが返される |
| TC-003 | 無効なメッセージ形式テスト | 無効な形式のメッセージを `/api/chat` エンドポイントに送信 | 適切なエラーレスポンスが返される |
| TC-004 | サービス例外処理テスト | サービスが例外をスローした場合の `/api/chat` エンドポイントの挙動をテスト | エラーが適切に処理され、クライアントにエラーレスポンスが返される |

## 3. サービス層テスト

### 3.1 AssistantManagerService

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TS-001 | OpenAPIスペック読み込みテスト | `load_openapi_spec` メソッドが正常にOpenAPIスペックを読み込めることをテスト | 有効なOpenAPIスペックが返される |
| TS-002 | OpenAPIスペックファイル不在テスト | スペックファイルが存在しない場合の `load_openapi_spec` メソッドの挙動をテスト | 適切な例外がスローされる |
| TS-003 | 無効なOpenAPIスペックテスト | 無効な形式のOpenAPIスペックファイルの場合の `load_openapi_spec` メソッドの挙動をテスト | JSONDecodeErrorがスローされる |
| TS-004 | OpenAPIツール作成テスト | `create_openapi_tool` メソッドが正常にツールを作成できることをテスト | 有効なOpenApiToolオブジェクトが返される |
| TS-005 | メッセージ処理成功テスト | `process_openapi_spec` メソッドが正常にメッセージを処理できることをテスト | 有効なレスポンスが返される |
| TS-006 | エージェント実行失敗テスト | エージェント実行が失敗した場合の `process_openapi_spec` メソッドの挙動をテスト | エラーレスポンスが返される |
| TS-007 | 予期しない例外処理テスト | 予期しない例外が発生した場合の `process_openapi_spec` メソッドの挙動をテスト | エラーレスポンスが返される |
| TS-008 | エージェント応答なしテスト | エージェントから応答がない場合の `process_openapi_spec` メソッドの挙動をテスト | "No response found"メッセージが返される |

## 4. ツール層テスト

### 4.1 SwaggerSpecTool

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TT-001 | 補助金APIツール作成テスト | `create_subsidies_tool` 関数が正常にOpenApiToolを作成できることをテスト | 有効なOpenApiToolオブジェクトが返される |
| TT-002 | ツールプロパティ検証テスト | 作成されたツールが正しい名前、説明、認証情報を持つことをテスト | 期待通りのプロパティを持つオブジェクトが返される |

### 4.2 BingGroundingTool (未実装テスト)

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TT-003 | Bing検索結果取得テスト | Bing検索から正常に結果を取得できることをテスト | 有効な検索結果が返される |
| TT-004 | 検索クエリ無効テスト | 無効な検索クエリの場合の挙動をテスト | 適切なエラーメッセージが返される |
| TT-005 | 検索結果なしテスト | 検索結果がない場合の挙動をテスト | 空の結果または適切なメッセージが返される |

## 5. 統合テスト

### 5.1 エンドツーエンドフロー

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TI-001 | 補助金クエリ完全フローテスト | ユーザーからの補助金に関する質問を受け、AIエージェントが処理し、OpenAPIを通じて補助金情報を取得するフローをテスト | 正確な補助金情報を含む応答が返される |
| TI-002 | 一般的な質問フローテスト | 補助金に関連しない一般的な質問をテストし、AIエージェントがどのように応答するかをテスト | 適切な応答または明確なエラーメッセージが返される |

### 5.2 エラー処理フロー

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| TI-003 | API接続エラーフローテスト | 外部APIへの接続が失敗した場合のシステムの挙動をテスト | ユーザーに分かりやすいエラーメッセージが返される |
| TI-004 | AIモデルタイムアウトフローテスト | AIモデルがタイムアウトした場合のシステムの挙動をテスト | 適切なエラーメッセージが返され、リトライメカニズムが機能する |

## 6. モック戦略

このプロジェクトのテストでは以下のコンポーネントをモック化します：

1. **AIProjectClient** - Azure AIプロジェクトクライアントとの実際の通信を避けるため
2. **OpenAPIスペックファイル** - テスト環境でのファイルI/Oを制御するため
3. **Azure AI ResponseRun** - エージェント実行結果をシミュレートするため
4. **メッセージリスト** - エージェントとのメッセージ交換をシミュレートするため

## 7. テストカバレッジ目標

| コンポーネント | カバレッジ目標 |
|--------------|--------------|
| モデル      | 90% |
| コントローラー | 85% |
| サービス    | 90% |
| ツール      | 85% |
| 全体        | 85% |

## 8. テスト実行手順

### 8.1 単体テスト実行

```bash
# プロジェクトのルートディレクトリから実行
cd app/backend
pytest tests/unit -v
```

### 8.2 統合テスト実行

```bash
# プロジェクトのルートディレクトリから実行
cd app/backend
pytest tests/integration -v
```

### 8.3 カバレッジレポート生成

```bash
# カバレッジレポート付きで全テスト実行
cd app/backend
pytest --cov=. --cov-report=html
```

## 9. モックサンプル

### 9.1 AIProjectClientのモック例

```python
# tests/unit/services/test_assistant_manager_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.assistant_manager_service import AssistantManagerService

@pytest.fixture
def mock_project_client():
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
    
    # 実行のモック
    run = Mock()
    run.status = "completed"
    run.last_error = None
    client.agents.create_and_process_run.return_value = run
    
    return client

def test_process_openapi_spec_success(mock_project_client):
    # テスト実装
    ...
```

## 10. テスト関連ディレクトリ構造

```
app/
  backend/
    tests/
      unit/
        models/
          test_models.py
        services/
          test_assistant_manager_service.py
        tools/
          actions/
            test_swagger_spec_tool.py
          knowledge/
            test_bing_grounding_tool.py
        test_controller.py
      integration/
        test_chat_flow.py
        test_error_handling.py
```

## 11. テストデータ

テストデータは `app/backend/tests/fixtures` ディレクトリに保存します。主要なテストデータには以下が含まれます：

1. サンプルOpenAPIスペック JSON
2. モックエージェント応答
3. モックエラーレスポンス
4. テスト用ユーザーメッセージ