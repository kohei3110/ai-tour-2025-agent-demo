# AI Tour 2025 Agent Demo 技術仕様書

## 1. システム概要

AI Tour 2025 Agent Demoは、Azure OpenAIを活用した補助金情報案内と申請書生成支援のためのAIエージェントシステムです。本システムは、以下の目的で開発されています：

- 補助金に関する質問に自然言語で応答する
- 補助金の検索と情報提供を行う
- 補助金申請書のテンプレート生成を支援する
- ユーザーのビジネス内容に合わせた申請書作成をサポートする

## 2. システムアーキテクチャ

### 2.1 全体構成

システムは、バックエンドとフロントエンドの2つの主要コンポーネントで構成されています：

```
AI Tour 2025 Agent Demo
├── バックエンド (Python/FastAPI)
│   ├── コントローラー層
│   ├── サービス層
│   ├── ツール層
│   └── モデル層
└── フロントエンド (React)
    ├── UIコンポーネント
    └── APIサービス
```

### 2.2 バックエンド詳細

#### 2.2.1 コントローラー層

FastAPIを使用したRESTful APIを提供します：

- **controller.py**: APIエンドポイント定義
  - `/api/health`: ヘルスチェック
  - `/api/chat`: チャットメッセージの送受信
  - `/api/application/generate`: 申請書テンプレート生成
  - `/api/generate`: 一般テキスト生成

#### 2.2.2 サービス層

主要なビジネスロジックを実装：

- **assistant_manager_service.py**: AIエージェントの管理
  - Azure AI Projects クライアント連携
  - エージェントとスレッドの管理
  - OpenAPIツールとの統合

#### 2.2.3 ツール層

補助機能を提供するツール群：

- **actions/swagger_spec_tool.py**: OpenAPIを使用した補助金情報検索
- **actions/application_doc_generator_tool.py**: 申請書テンプレート生成
- **knowledge/bing_grounding_tool.py**: 最新情報検索（計画中）
- **common_utils.py**: 共通ユーティリティ関数

#### 2.2.4 モデル層

データ構造の定義：

- **models/models.py**: Pydanticモデル
  - `MessageRequest`: チャットメッセージリクエスト
  - `ApplicationFormRequest`: 申請書テンプレート生成リクエスト
  - `PromptRequest`: テキスト生成リクエスト

### 2.3 フロントエンド詳細

Reactベースのシングルページアプリケーション：

- **App.js**: メインアプリケーションコンポーネント
- **services/api.js**: バックエンドAPI通信

## 3. データフロー

### 3.1 チャット会話フロー

1. ユーザーがフロントエンドからメッセージを送信
2. バックエンドの`/api/chat`エンドポイントがリクエストを受信
3. `AssistantManagerService`がAzure AIプロジェクトクライアントを使用してエージェントとやり取り
4. エージェントが必要に応じて`SwaggerSpecTool`を使用して補助金情報を検索
5. 生成された回答がユーザーに返される

### 3.2 申請書テンプレート生成フロー

1. ユーザーが補助金情報とビジネス概要を入力
2. バックエンドの`/api/application/generate`エンドポイントがリクエストを受信
3. `ApplicationFormGenerator`が補助金情報を基にテンプレートを生成
4. ビジネス概要が提供されている場合、AIを使用してカスタマイズされたテンプレートを生成
5. 生成されたテンプレートがユーザーに返される

## 4. 外部依存関係

### 4.1 Azure Services

- **Azure OpenAI**: 自然言語処理と生成AIの基盤
- **Azure AI Projects**: AIエージェント管理

### 4.2 その他の依存関係

- **FastAPI**: バックエンドWebフレームワーク
- **React**: フロントエンドフレームワーク
- **Poetry**: Pythonパッケージ管理
- **pytest**: テストフレームワーク

## 5. セキュリティ設計

### 5.1 認証と認可

- Azure DefaultAzureCredentialを使用した認証
- ロールベースのアクセス制御（計画中）

### 5.2 データ保護

- センシティブなユーザーデータの保存なし
- セッションベースの一時的な会話管理

## 6. スケーラビリティと可用性

### 6.1 スケーリング戦略

- コンテナ化されたバックエンドサービス
- 水平スケーリングのサポート（計画中）

### 6.2 可用性設計

- ヘルスチェックエンドポイント
- エラー処理とリカバリーメカニズム

## 7. モニタリングと運用

### 7.1 ログ記録

- 構造化ロギング
- エラーと例外の適切なキャプチャ

### 7.2 メトリクス

- API呼び出し回数
- レスポンス時間
- エラー率

## 8. 開発およびテスト戦略

### 8.1 開発プロセス

- テスト駆動開発（TDD）アプローチ
- Gitフロー開発モデル

### 8.2 テスト戦略

- 単体テスト: 個々のコンポーネントのテスト
- 統合テスト: コンポーネント間の相互作用のテスト
- エンドツーエンドテスト: 完全なユーザーフローのテスト

## 9. デプロイメントプロセス

### 9.1 環境

- 開発環境
- ステージング環境
- 本番環境

### 9.2 CI/CD

- 自動テスト実行
- コンテナイメージのビルドと公開
- 環境ごとの段階的デプロイ

## 10. 将来の拡張計画

- Bing検索による最新の補助金情報の取得
- 複数の言語サポート
- より高度な補助金マッチングアルゴリズム
- ユーザーフィードバックを基にした継続的改善

## 11. 制約事項

- Azure OpenAIの呼び出し制限
- 公開されている補助金情報の範囲内での対応
- モデルの知識のカットオフ日以降の情報については外部検索が必要

## 付録

### A. API詳細仕様

#### A.1 `/api/health` エンドポイント

- **メソッド**: GET
- **レスポンス**:
  ```json
  {
    "status": "ok"
  }
  ```

#### A.2 `/api/chat` エンドポイント

- **メソッド**: POST
- **リクエスト本文**:
  ```json
  {
    "message": "中小企業向けの最新の補助金について教えてください"
  }
  ```
- **レスポンス**: エージェントからのテキスト応答

#### A.3 `/api/application/generate` エンドポイント

- **メソッド**: POST
- **リクエスト本文**:
  ```json
  {
    "subsidy_info": {
      "title": "中小企業デジタル化支援補助金",
      "acceptance_start_datetime": "2025-04-01T09:00:00",
      "acceptance_end_datetime": "2025-05-31T17:00:00",
      "target_area_search": "全国",
      "subsidy_max_limit": 5000000,
      "target_number_of_employees": "5~50人"
    },
    "business_description": "IoTデバイスを活用した農業向けシステム開発"
  }
  ```
- **レスポンス**:
  ```json
  {
    "template": "申請書テンプレートのテキスト",
    "ai_enhanced": true
  }
  ```

#### A.4 `/api/generate` エンドポイント

- **メソッド**: POST
- **リクエスト本文**:
  ```json
  {
    "prompt": "補助金申請書の書き方のポイントを5つ教えてください"
  }
  ```
- **レスポンス**:
  ```json
  {
    "generated_text": "生成されたテキスト",
    "success": true
  }
  ```

### B. エラーコードとメッセージ

| エラーコード | メッセージ | 説明 |
|------------|----------|------|
| 400 | 補助金情報が必要です | 申請書生成に必要な補助金情報が提供されていない |
| 400 | プロンプトが必要です | テキスト生成に必要なプロンプトが提供されていない |
| 500 | 申請書テンプレート生成中にエラーが発生しました | 申請書生成処理中の内部エラー |
| 500 | メッセージ生成中にエラーが発生しました | AIテキスト生成中の内部エラー |
| 500 | エージェントの実行に失敗しました | AIエージェント実行中のエラー |

### C. データモデル

#### C.1 MessageRequest

```python
class MessageRequest(BaseModel):
    message: str
```

#### C.2 ApplicationFormRequest

```python
class ApplicationFormRequest(BaseModel):
    subsidy_info: Dict[str, Any] = Field(
        ..., 
        description="補助金の情報を含む辞書。title, acceptance_start_datetime, acceptance_end_datetime, target_area_search, subsidy_max_limit, target_number_of_employees などの情報"
    )
    business_description: Optional[str] = Field(
        None,
        description="AI拡張テンプレートを生成する場合のビジネスの説明文。例: 'IT企業向けクラウドサービス開発'"
    )
```

#### C.3 PromptRequest

```python
class PromptRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="AIに送信するプロンプト"
    )
```