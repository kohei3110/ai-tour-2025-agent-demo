import pytest
from unittest.mock import Mock
from tools.actions.application_doc_generator_tool import generate_application_text, ApplicationFormGenerator

class TestApplicationDocGeneratorTool:
    
    def test_generate_application_text_with_valid_data(self):
        """有効な補助金情報から申請書用のテキストを正しく生成できることをテスト"""
        # テスト用の補助金情報
        subsidy_info = {
            "title": "小規模事業者持続化補助金",
            "target_area_search": "東京都",
            "subsidy_max_limit": 50000000,
            "acceptance_start_datetime": "2024-04-01T10:00:00Z",
            "acceptance_end_datetime": "2024-05-30T17:00:00Z",
            "target_number_of_employees": "20名以下"
        }
        
        # 関数呼び出し
        result = generate_application_text(subsidy_info)
        
        # 検証
        assert "【申請書類：小規模事業者持続化補助金】" in result
        assert "申請期間：2024年4月1日～2024年5月30日" in result
        assert "対象地域：東京都" in result
        assert "補助上限額：5,000万円" in result
        assert "従業員数制限：20名以下" in result
        assert "申請理由：" in result
        
    def test_generate_application_text_with_missing_fields(self):
        """一部の情報が欠けている場合でも適切に処理されることをテスト"""
        # 一部情報が欠けた補助金情報
        subsidy_info = {
            "title": "起業支援補助金",
            "subsidy_max_limit": 1000000,
            # acceptance_start_datetime と acceptance_end_datetime が欠けている
            # target_area_search が欠けている
        }
        
        # 関数呼び出し
        result = generate_application_text(subsidy_info)
        
        # 検証
        assert "【申請書類：起業支援補助金】" in result
        assert "補助上限額：100万円" in result
        assert "申請期間：情報なし" in result
        assert "対象地域：情報なし" in result
        
    def test_application_form_generator_initialization(self):
        """ApplicationFormGeneratorクラスが正しく初期化されることをテスト"""
        # インスタンス化
        generator = ApplicationFormGenerator()
        
        # 検証
        assert hasattr(generator, 'generate_application_text')
        
    def test_application_form_generator_generate_method(self):
        """ApplicationFormGeneratorクラスのgeneratメソッドが正しく動作することをテスト"""
        # テスト用の補助金情報
        subsidy_info = {
            "title": "創業支援補助金",
            "target_area_search": "全国",
            "subsidy_max_limit": 3000000,
            "acceptance_start_datetime": "2024-06-01T00:00:00Z",
            "acceptance_end_datetime": "2024-07-31T23:59:59Z"
        }
        
        # インスタンス化と関数呼び出し
        generator = ApplicationFormGenerator()
        result = generator.generate(subsidy_info)
        
        # 検証
        assert "【申請書類：創業支援補助金】" in result
        assert "申請期間：2024年6月1日～2024年7月31日" in result
        assert "対象地域：全国" in result
        assert "補助上限額：300万円" in result