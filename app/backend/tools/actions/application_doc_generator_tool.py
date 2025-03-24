import re
import datetime
from typing import Dict, Any, Optional

def format_currency_ja(amount: int) -> str:
    """
    金額を日本語表記にフォーマットする
    
    Args:
        amount: 数値（円）
        
    Returns:
        フォーマットされた金額文字列
    """
    if amount >= 100000000:  # 1億円以上
        value = amount / 100000000
        return f"{value:,.0f}億円"
    elif amount >= 10000:  # 1万円以上
        value = amount / 10000
        return f"{value:,.0f}万円"
    else:
        return f"{amount:,}円"
    
def format_date_ja(date_str: Optional[str]) -> str:
    """
    ISO形式の日付文字列を「YYYY年MM月DD日」形式にフォーマットする
    
    Args:
        date_str: ISO形式の日付文字列（例: 2024-04-01T10:00:00Z）
        
    Returns:
        日本語形式の日付文字列
    """
    if not date_str:
        return "情報なし"
    
    try:
        # ISO形式の日付文字列をdatetimeオブジェクトに変換
        date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # JSTタイムゾーンを考慮して日本時間に調整 (UTC+9)
        date_obj = date_obj + datetime.timedelta(hours=9)
        # 「YYYY年MM月DD日」形式にフォーマット
        return date_obj.strftime("%Y年%m月%d日")
    except (ValueError, TypeError):
        return "無効な日付"

def generate_application_text(subsidy_info: Dict[str, Any]) -> str:
    """
    補助金情報から申請書用のテキストを生成する
    
    Args:
        subsidy_info: 補助金の情報を含む辞書
        
    Returns:
        申請書用のテキスト
    """
    # タイトル
    title = subsidy_info.get("title", "不明な補助金")
    
    # 申請期間の処理
    start_date = format_date_ja(subsidy_info.get("acceptance_start_datetime"))
    end_date = format_date_ja(subsidy_info.get("acceptance_end_datetime"))
    
    if start_date != "情報なし" and end_date != "情報なし" and start_date != "無効な日付" and end_date != "無効な日付":
        application_period = f"{start_date}～{end_date}"
    else:
        application_period = "情報なし"
    
    # 対象地域
    target_area = subsidy_info.get("target_area_search", "情報なし")
    
    # 補助上限額
    max_limit = subsidy_info.get("subsidy_max_limit")
    if max_limit is not None:
        max_limit_str = format_currency_ja(max_limit)
    else:
        max_limit_str = "情報なし"
    
    # 従業員数制限
    employee_limit = subsidy_info.get("target_number_of_employees", "情報なし")
    
    # テキスト生成
    application_text = f"""【申請書類：{title}】

■基本情報
申請期間：{application_period}
対象地域：{target_area}
補助上限額：{max_limit_str}
"""

    # 従業員数制限があれば追加
    if employee_limit != "情報なし":
        application_text += f"従業員数制限：{employee_limit}\n"
    
    # 申請理由のテンプレート
    application_text += """
■申請理由：
[ここに補助金申請の具体的な理由を記入してください。例：
・事業の現状と課題
・補助金を活用した事業計画の概要
・期待される効果や成果
・予算計画の概要]

■事業計画概要：
[ここに具体的な事業計画を記入してください。計画の実現可能性、革新性、市場性、社会的意義などを明確に説明すると効果的です。]

■実施体制：
[ここに事業実施体制について記入してください。担当者の役割や外部との連携体制などを含めると良いでしょう。]

■スケジュール：
[ここに事業の実施スケジュールを記入してください。マイルストーンとなる重要な日程も含めると良いでしょう。]

■予算計画：
[ここに予算計画の詳細を記入してください。各費目ごとの金額と、その積算根拠を明確に示すことが重要です。]

■期待される効果：
[ここに補助金による事業実施で期待される具体的な効果を記入してください。定量的な指標と定性的な効果の両方を含めると良いでしょう。]
"""
    
    return application_text

class ApplicationFormGenerator:
    """
    補助金申請書類テキスト生成ツール
    """
    
    def __init__(self):
        """初期化"""
        self.generate_application_text = generate_application_text
    
    def generate(self, subsidy_info: Dict[str, Any]) -> str:
        """
        補助金情報から申請書用のテキストを生成する
        
        Args:
            subsidy_info: 補助金の情報を含む辞書
            
        Returns:
            申請書用のテキスト
        """
        return self.generate_application_text(subsidy_info)