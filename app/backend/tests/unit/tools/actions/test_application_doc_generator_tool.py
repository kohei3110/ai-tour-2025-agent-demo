import unittest
from unittest.mock import patch, MagicMock
import datetime
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
import logging

# Mock the azure.ai.projects module before importing the application_doc_generator_tool
mock_assistant = MagicMock()
with patch.dict('sys.modules', {'azure.ai.projects': mock_assistant}):
    from tools.actions.application_doc_generator_tool import (
        format_currency_ja, 
        format_date_ja, 
        generate_application_text,
        ApplicationFormGenerator,
        request_ai_content
    )

class TestFormatCurrencyJa(unittest.TestCase):
    """金額フォーマッティング機能のテスト"""
    
    def test_format_large_amount(self):
        """1億円以上の金額のフォーマット"""
        result = format_currency_ja(1000000000)
        self.assertEqual(result, "10億円")
        
    def test_format_medium_amount(self):
        """1万円以上の金額のフォーマット"""
        result = format_currency_ja(5000000)
        self.assertEqual(result, "500万円")
        
    def test_format_small_amount(self):
        """1万円未満の金額のフォーマット"""
        result = format_currency_ja(5000)
        self.assertEqual(result, "5,000円")

class TestFormatDateJa(unittest.TestCase):
    """日付フォーマッティング機能のテスト"""
    
    def test_format_valid_date(self):
        """有効な日付のフォーマット"""
        result = format_date_ja("2024-04-01T10:00:00Z")
        self.assertEqual(result, "2024年04月01日")
        
    def test_format_empty_date(self):
        """空の日付のフォーマット"""
        result = format_date_ja(None)
        self.assertEqual(result, "情報なし")
        
    def test_format_invalid_date(self):
        """無効な日付のフォーマット"""
        result = format_date_ja("invalid-date")
        self.assertEqual(result, "無効な日付")

class TestGenerateApplicationText(unittest.TestCase):
    """申請書テキスト生成機能のテスト"""
    
    def test_generate_complete_application(self):
        """全ての情報が揃っている場合の申請書生成"""
        subsidy_info = {
            "title": "テスト補助金",
            "acceptance_start_datetime": "2024-04-01T00:00:00Z",
            "acceptance_end_datetime": "2024-05-31T23:59:59Z",
            "target_area_search": "全国",
            "subsidy_max_limit": 10000000,
            "target_number_of_employees": "300人以下"
        }
        
        result = generate_application_text(subsidy_info)
        
        self.assertIn("【申請書類：テスト補助金】", result)
        self.assertIn("申請期間：2024年04月01日～2024年05月31日", result)
        self.assertIn("対象地域：全国", result)
        self.assertIn("補助上限額：1,000万円", result)
        self.assertIn("従業員数制限：300人以下", result)
        self.assertIn("■申請理由：", result)
        
    def test_generate_minimal_application(self):
        """最小限の情報での申請書生成"""
        subsidy_info = {
            "title": "最小限補助金"
        }
        
        result = generate_application_text(subsidy_info)
        
        self.assertIn("【申請書類：最小限補助金】", result)
        self.assertIn("申請期間：情報なし", result)
        self.assertIn("対象地域：情報なし", result)
        self.assertIn("補助上限額：情報なし", result)
        self.assertNotIn("従業員数制限", result)
        self.assertIn("■申請理由：", result)

class TestAIEnhancedApplicationGenerator(unittest.TestCase):
    """AI拡張申請書生成機能のテスト"""
    
    @patch('tools.actions.application_doc_generator_tool.request_ai_content')
    def test_generate_ai_enhanced_application(self, mock_request_ai_content):
        """AIによる内容拡張機能のテスト"""
        # AIサービスのモック応答を設定
        mock_ai_response = {
            "application_reason": "当社は創業5年のITスタートアップで、クラウドサービス事業を展開しています。現在、事業拡大のためのクラウドインフラ強化が必要な状況です。",
            "business_plan": "本補助金を活用し、次世代クラウドプラットフォームの開発と市場展開を行います。具体的には、AIを活用した予測分析機能を実装します。",
            "implementation_structure": "プロジェクトマネージャー1名、開発エンジニア3名、マーケティング担当1名の体制で実施します。",
            "schedule": "7月: 要件定義、8-9月: 開発フェーズ、10月: テスト、11-12月: 市場投入",
            "budget_plan": "開発人件費: 500万円、クラウドインフラ費: 300万円、マーケティング費: 200万円",
            "expected_effects": "売上30%増加、顧客満足度15%向上、運用コスト20%削減を見込んでいます。"
        }
        mock_request_ai_content.return_value = mock_ai_response
        
        # テスト用の補助金情報
        subsidy_info = {
            "title": "IT導入補助金",
            "acceptance_start_datetime": "2024-04-01T00:00:00Z",
            "acceptance_end_datetime": "2024-05-31T23:59:59Z",
            "target_area_search": "全国",
            "subsidy_max_limit": 10000000,
            "target_number_of_employees": "300人以下",
            "summary": "ITツール導入による生産性向上を支援する補助金です。",
            "target_field": "情報通信業",
            "target_type": "中小企業"
        }
        
        # ApplicationFormGeneratorのインスタンスを作成
        generator = ApplicationFormGenerator()
        
        # AI拡張申請書を生成
        result = generator.generate_ai_enhanced(subsidy_info, "IT企業向けクラウドサービス開発")
        
        # モックが正しく呼び出されたことを確認
        mock_request_ai_content.assert_called_once()
        
        # 結果に期待される内容が含まれていることを確認
        self.assertIn("【申請書類：IT導入補助金】", result)
        self.assertIn("申請期間：2024年04月01日～2024年05月31日", result)
        self.assertIn("対象地域：全国", result)
        self.assertIn("補助上限額：1,000万円", result)
        
        # AI生成コンテンツが含まれていることを確認
        self.assertIn("当社は創業5年のITスタートアップで", result)
        self.assertIn("次世代クラウドプラットフォームの開発", result)
        self.assertIn("プロジェクトマネージャー1名", result)
        self.assertIn("7月: 要件定義", result)
        self.assertIn("開発人件費: 500万円", result)
        self.assertIn("売上30%増加", result)
    
    @patch('tools.actions.application_doc_generator_tool.request_ai_content')
    def test_ai_service_error_handling(self, mock_request_ai_content):
        """AIサービスエラー時の処理テスト"""
        # AIサービスがエラーを返すケース
        mock_request_ai_content.side_effect = Exception("AI service unavailable")
        
        subsidy_info = {
            "title": "IT導入補助金",
            "subsidy_max_limit": 10000000
        }
        
        generator = ApplicationFormGenerator()
        
        # AI拡張に失敗しても、基本テンプレートは生成されるべき
        result = generator.generate_ai_enhanced(subsidy_info, "IT企業向けサービス")
        
        # 基本情報は含まれている
        self.assertIn("【申請書類：IT導入補助金】", result)
        self.assertIn("補助上限額：1,000万円", result)
        
        # エラーメッセージが含まれている
        self.assertIn("※AI拡張機能は現在利用できません", result)

class TestRequestAIContent(unittest.TestCase):
    """AIコンテンツ生成機能のテスト"""
    
    @patch('tools.actions.application_doc_generator_tool.AIProjectClient')
    @patch('tools.actions.application_doc_generator_tool.AssistantManagerService')
    def test_request_ai_content_success(self, mock_service_class, mock_client_class):
        """AIサービスによる内容生成の成功パターンテスト"""
        # モックのレスポンス設定
        mock_instance = mock_service_class.return_value
        mock_instance.process_openapi_spec.return_value = '''```json
{
    "application_reason": "テスト理由",
    "business_plan": "テスト計画",
    "implementation_structure": "テスト体制",
    "schedule": "テストスケジュール",
    "budget_plan": "テスト予算",
    "expected_effects": "テスト効果"
}```'''

        # テストデータ
        subsidy_info = {
            "title": "テスト補助金",
            "summary": "テスト用の補助金です",
            "target_field": "IT",
            "target_type": "中小企業",
            "subsidy_max_limit": 1000000
        }
        business_description = "テストビジネス"

        # 環境変数の設定
        with patch.dict('os.environ', {
            'AZURE_AI_PROJECT_ID': 'test-id',
            'AZURE_AI_API_KEY': 'test-key',
            'AZURE_AI_ENDPOINT': 'test-endpoint'
        }):
            # 関数実行
            result = request_ai_content(subsidy_info, business_description)

        # 検証
        mock_service_class.assert_called_once_with(mock_client_class.return_value)
        mock_instance.process_openapi_spec.assert_called_once()
        self.assertEqual(result["application_reason"], "テスト理由")
        self.assertEqual(result["business_plan"], "テスト計画")
        self.assertEqual(result["implementation_structure"], "テスト体制")
        self.assertEqual(result["schedule"], "テストスケジュール")
        self.assertEqual(result["budget_plan"], "テスト予算")
        self.assertEqual(result["expected_effects"], "テスト効果")

    @patch('tools.actions.application_doc_generator_tool.AIProjectClient')
    @patch('tools.actions.application_doc_generator_tool.AssistantManagerService')
    def test_request_ai_content_non_json_response(self, mock_service_class, mock_client_class):
        """JSON以外のレスポンスを処理できることのテスト"""
        # モックのレスポンス設定（JSONでない形式）
        mock_instance = mock_service_class.return_value
        mock_instance.process_openapi_spec.return_value = """
application_reason: テスト理由
business_plan: テスト計画
implementation_structure: テスト体制
schedule: テストスケジュール
budget_plan: テスト予算
expected_effects: テスト効果
"""

        # テストデータ
        subsidy_info = {
            "title": "テスト補助金",
            "summary": "テスト用の補助金です"
        }
        business_description = "テストビジネス"

        # 環境変数の設定
        with patch.dict('os.environ', {
            'AZURE_AI_PROJECT_ID': 'test-id',
            'AZURE_AI_API_KEY': 'test-key',
            'AZURE_AI_ENDPOINT': 'test-endpoint'
        }):
            # 関数実行
            result = request_ai_content(subsidy_info, business_description)

        # 検証
        self.assertIn("application_reason", result)
        self.assertIn("business_plan", result)
        self.assertIn("implementation_structure", result)
        self.assertIn("schedule", result)
        self.assertIn("budget_plan", result)
        self.assertIn("expected_effects", result)

    @patch('tools.actions.application_doc_generator_tool.AIProjectClient')
    @patch('tools.actions.application_doc_generator_tool.AssistantManagerService')
    def test_request_ai_content_service_error(self, mock_service_class, mock_client_class):
        """AIサービスがエラーを返す場合のテスト"""
        # モックのエラー設定
        mock_instance = mock_service_class.return_value
        mock_instance.process_openapi_spec.side_effect = Exception("テストエラー")

        # テストデータ
        subsidy_info = {"title": "テスト補助金"}
        business_description = "テストビジネス"

        # 環境変数の設定
        with patch.dict('os.environ', {
            'AZURE_AI_PROJECT_ID': 'test-id',
            'AZURE_AI_API_KEY': 'test-key',
            'AZURE_AI_ENDPOINT': 'test-endpoint'
        }):
            # エラーが発生することを確認
            with self.assertRaises(Exception) as context:
                request_ai_content(subsidy_info, business_description)

        self.assertIn("AIコンテンツ生成エラー", str(context.exception))

# テスト用データ
@pytest.fixture
def sample_subsidy_info():
    return {
        "title": "中小企業デジタル化支援補助金",
        "summary": "中小企業のデジタル化を支援する補助金です",
        "target_field": "IT・情報通信",
        "target_type": "中小企業",
        "subsidy_max_limit": 1000000
    }

@pytest.fixture
def sample_business_description():
    return "当社は動物病院向けのクラウド型電子カルテシステムを開発しています。"

@pytest.fixture
def mock_ai_response():
    return {
        "application_reason": "当社のクラウド型電子カルテシステムは、動物病院のデジタル化を促進します。",
        "business_plan": "全国の動物病院に向けたクラウド型電子カルテの展開を計画しています。",
        "implementation_structure": "開発部門5名とサポート部門3名の体制で実施します。",
        "schedule": "2025年Q2にベータ版リリース、Q3に本格展開を予定しています。",
        "budget_plan": "システム開発費600万円、サーバー構築費200万円、マーケティング費用200万円を予定。",
        "expected_effects": "導入病院の業務効率が30%向上し、医療ミスを50%削減できると見込んでいます。"
    }

class TestApplicationDocGeneratorTool:
    
    @pytest.mark.asyncio
    @patch('tools.actions.application_doc_generator_tool.AssistantManagerService')
    async def test_request_ai_content_success(self, mock_service_class, sample_subsidy_info, sample_business_description, mock_ai_response):
        """AIサービスから正常にコンテンツを取得できる場合のテスト"""
        # AIサービスのモックを設定
        mock_service_instance = AsyncMock()
        mock_service_class.return_value = mock_service_instance
        
        # JSONレスポンスをモック
        mock_service_instance.process_openapi_spec.return_value = json.dumps(mock_ai_response)
        
        # 関数を実行
        result = await request_ai_content(sample_subsidy_info, sample_business_description)
        
        # 検証
        assert result == mock_ai_response
        mock_service_instance.process_openapi_spec.assert_called_once()
        # プロンプトにビジネス概要と補助金情報が含まれていることを確認
        prompt_arg = mock_service_instance.process_openapi_spec.call_args[0][0]
        assert sample_business_description in prompt_arg
        assert sample_subsidy_info["title"] in prompt_arg
    
    @pytest.mark.asyncio
    @patch('tools.actions.application_doc_generator_tool.AssistantManagerService')
    async def test_request_ai_content_with_code_block(self, mock_service_class, sample_subsidy_info, sample_business_description, mock_ai_response):
        """マークダウンコードブロック形式のJSONレスポンスを処理できることをテスト"""
        # AIサービスのモックを設定
        mock_service_instance = AsyncMock()
        mock_service_class.return_value = mock_service_instance
        
        # マークダウンコードブロック形式のJSONレスポンスをモック
        json_response = f"```json\n{json.dumps(mock_ai_response, indent=2)}\n```"
        mock_service_instance.process_openapi_spec.return_value = json_response
        
        # 関数を実行
        result = await request_ai_content(sample_subsidy_info, sample_business_description)
        
        # 検証
        assert result == mock_ai_response
    
    @pytest.mark.asyncio
    @patch('tools.actions.application_doc_generator_tool.AssistantManagerService')
    @patch('tools.actions.application_doc_generator_tool.logger')
    async def test_request_ai_content_exception(self, mock_logger, mock_service_class, sample_subsidy_info, sample_business_description):
        """例外が発生した場合のテスト"""
        # AIサービスのモックを設定して例外を発生させる
        mock_service_instance = AsyncMock()
        mock_service_class.return_value = mock_service_instance
        mock_service_instance.process_openapi_spec.side_effect = Exception("Test error")
        
        # 関数を実行し、例外が再発生することを確認
        with pytest.raises(Exception) as excinfo:
            await request_ai_content(sample_subsidy_info, sample_business_description)
        
        # 例外メッセージを検証
        assert "AIコンテンツ生成エラー" in str(excinfo.value)
        # ロギングを検証
        mock_logger.error.assert_called_once()

class TestApplicationFormGenerator:
    
    def test_generate(self, sample_subsidy_info):
        """基本的な申請書テキスト生成が機能することをテスト"""
        generator = ApplicationFormGenerator()
        result = generator.generate(sample_subsidy_info)
        
        # 申請書テキストに補助金情報が含まれているか確認
        assert sample_subsidy_info["title"] in result
        assert "申請理由" in result
        assert "事業計画概要" in result
    
    @pytest.mark.asyncio
    @patch('tools.actions.application_doc_generator_tool.request_ai_content')
    async def test_generate_ai_enhanced(self, mock_request_ai, sample_subsidy_info, sample_business_description, mock_ai_response):
        """AI拡張された申請書テキスト生成が機能することをテスト"""
        # モックを設定
        mock_request_ai.return_value = mock_ai_response
        
        # 生成器のインスタンスを作成
        generator = ApplicationFormGenerator()
        
        # AI拡張テキストを生成
        result = await generator.generate_ai_enhanced(sample_subsidy_info, sample_business_description)
        
        # 検証
        assert sample_subsidy_info["title"] in result
        assert mock_ai_response["application_reason"] in result
        assert mock_ai_response["business_plan"] in result
        assert mock_ai_response["expected_effects"] in result
        # AIによる生成物であることを示す文言があることを確認
        assert "生成AIによって作成されました" in result
    
    @pytest.mark.asyncio
    @patch('tools.actions.application_doc_generator_tool.request_ai_content')
    @patch('tools.actions.application_doc_generator_tool.logger')
    async def test_generate_ai_enhanced_error(self, mock_logger, mock_request_ai, sample_subsidy_info, sample_business_description):
        """AI拡張失敗時に基本テンプレートが返されることをテスト"""
        # モックを設定して例外を発生させる
        mock_request_ai.side_effect = Exception("Test error")
        
        # 生成器のインスタンスを作成
        generator = ApplicationFormGenerator()
        
        # AI拡張テキストを生成（エラーが発生するケース）
        result = await generator.generate_ai_enhanced(sample_subsidy_info, sample_business_description)
        
        # 検証
        assert sample_subsidy_info["title"] in result
        assert "AI拡張機能は現在利用できません" in result
        # ロギングを検証
        mock_logger.error.assert_called_once()