# AI Tour 2025 Agent Demo

## プロジェクト概要

AI Tour 2025 Agent Demoは、Azure OpenAIを活用した補助金情報案内と申請書生成支援のためのAIエージェントシステムです。ユーザーは自然言語で補助金に関する質問を行い、AIエージェントが適切な補助金情報を検索・提供します。また、補助金申請に必要な申請書の作成支援も行います。

## 主な機能

1. **補助金情報検索・案内**：ユーザーの質問に応じて、適切な補助金情報を提供
2. **申請書テンプレート生成**：補助金情報を基に申請書テンプレートを自動生成
3. **AI拡張テンプレート生成**：ビジネス概要を基にカスタマイズされた申請書を生成
4. **一般的な質問応答**：補助金以外の一般的な質問にも対応

## 技術スタック

### バックエンド
- Python 3.12
- FastAPI
- Azure AI Projects (Azure OpenAI)
- 自動テストフレームワーク (pytest)

### フロントエンド
- React
- JavaScript/CSS

## アーキテクチャ

本システムは以下のコンポーネントで構成されています：

### バックエンド層

1. **コントローラー層**
   - APIエンドポイントを提供
   - リクエスト処理とレスポンス返却

2. **サービス層**
   - AssistantManagerService: AIエージェントとの対話管理

3. **ツール層**
   - Swagger Spec Tool: OpenAPIを使用した補助金情報検索
   - Application Document Generator: 申請書テンプレート生成
   - Bing Grounding Tool: 補助金に関する最新情報検索（計画中）

4. **モデル層**
   - データモデルとバリデーション（Pydantic）

### フロントエンド層

- ユーザーインターフェース（チャットUI）
- 補助金申請書作成UI

## API仕様

### 1. ヘルスチェックエンドポイント
- **エンドポイント**: `/api/health`
- **メソッド**: GET
- **説明**: アプリケーションの稼働状態を確認
- **レスポンス**: `{"status": "ok"}`

### 2. チャットエンドポイント
- **エンドポイント**: `/api/chat`
- **メソッド**: POST
- **説明**: AIエージェントに対して補助金に関する質問を送信
- **リクエスト本文**: 
  ```json
  {
    "message": "中小企業向けの最新の補助金について教えてください"
  }
  ```
- **レスポンス**: AIエージェントからのテキスト応答

### 3. 申請書テンプレート生成エンドポイント
- **エンドポイント**: `/api/application/generate`
- **メソッド**: POST
- **説明**: 補助金情報を基にした申請書テンプレートを生成
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

### 4. テキスト生成エンドポイント
- **エンドポイント**: `/api/generate`
- **メソッド**: POST
- **説明**: 任意のプロンプトに対してAIがテキストを生成
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

## 開発環境セットアップ

### 前提条件
- Python 3.12以上
- Node.js 18以上
- Azure サブスクリプション（Azure OpenAI利用のため）

### バックエンドのセットアップ
```bash
# 依存関係のインストール
cd app/backend
poetry install

# 開発サーバーの起動
poetry run uvicorn startup:app --reload
```

### フロントエンドのセットアップ
```bash
# 依存関係のインストール
cd app/frontend
npm install

# 開発サーバーの起動
npm start
```

## テスト

本プロジェクトはテスト駆動開発(TDD)の原則に従って開発されています。

```bash
# バックエンドのテスト実行
cd app/backend
poetry run pytest

# カバレッジレポート付きのテスト実行
poetry run pytest --cov=. --cov-report=html
```

## デプロイ

### Dockerを使用したデプロイ
```bash
# バックエンドのビルド
cd app/backend
docker build -t ai-tour-agent-backend .

# フロントエンドのビルド
cd app/frontend
npm run build
```

## ライセンス

Copyright (c) Microsoft Corporation. All rights reserved.