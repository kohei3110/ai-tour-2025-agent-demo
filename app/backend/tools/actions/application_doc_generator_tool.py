"""
補助金申請書類生成ツール
"""

import os
import re
import json
import logging
from typing import Dict, Any
from tools.common_utils import format_currency_ja, format_date_ja, generate_application_text
from services.assistant_manager_service import AssistantManagerService
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client: AIProjectClient = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
)

# ロガーの設定
logger = logging.getLogger(__name__)

async def request_ai_content(subsidy_info: Dict[str, Any], business_description: str) -> Dict[str, str]:
    """
    Azure AI Agent Serviceを使用して申請書の内容を生成する
    
    Args:
        subsidy_info: 補助金情報の辞書
        business_description: ビジネスの簡単な説明
        
    Returns:
        生成された申請書コンテンツを含む辞書
    
    Raises:
        Exception: AIサービスとの通信エラー、または応答解析エラー時
    """
    try:        # AIエージェントサービスのインスタンスを取得
        service = AssistantManagerService(project_client)
        
        # AIエージェントに送信するプロンプトを構築
        prompt = f"""
補助金申請書の主要セクションの内容を生成してください。以下の補助金情報とビジネス概要に基づいて、申請に適した内容を作成してください。

## 補助金情報
- 名称: {subsidy_info.get('title', '不明')}
- 概要: {subsidy_info.get('summary', '情報なし')}
- 対象分野: {subsidy_info.get('target_field', '情報なし')}
- 対象者: {subsidy_info.get('target_type', '情報なし')}
- 補助上限額: {format_currency_ja(subsidy_info.get('subsidy_max_limit', 0)) if subsidy_info.get('subsidy_max_limit') is not None else '情報なし'}

## ビジネス概要
{business_description}

以下の各セクションの内容を、明確かつ説得力のある形で日本語で生成してください：

1. application_reason: 申請理由（事業の現状と課題、補助金活用の目的）
2. business_plan: 事業計画の概要（実現可能性、革新性、市場性、社会的意義）
3. implementation_structure: 実施体制（担当者の役割や外部との連携）
4. schedule: 実施スケジュール（主要なマイルストーン）
5. budget_plan: 予算計画（主要な費目と金額）
6. expected_effects: 期待される効果（定量的・定性的な効果）

それぞれのセクションは具体的かつ簡潔に、150字程度で記述してください。JSONフォーマットで返答してください。
        """
        
        # AIエージェントにリクエストを送信
        response = await service.process_openapi_spec(prompt)
        
        # 応答からJSON部分を抽出して解析
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            content_json = json_match.group(1)
            return json.loads(content_json)
        
        # JSON形式でない場合、テキスト全体を解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # JSONとして解析できない場合は、手動でパースを試みる
            result = {}
            sections = ["application_reason", "business_plan", "implementation_structure", 
                       "schedule", "budget_plan", "expected_effects"]
            
            for section in sections:
                pattern = rf"{section}[:：]\s*(.*?)(?=\n\n|\Z)"
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    result[section] = match.group(1).strip()
                else:
                    result[section] = f"{section}の情報は生成できませんでした。"
            
            return result
    
    except Exception as e:
        logger.error(f"AI content generation error: {str(e)}")
        raise Exception(f"AIコンテンツ生成エラー: {str(e)}")

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
    
    async def generate_ai_enhanced(self, subsidy_info: Dict[str, Any], business_description: str) -> str:
        """
        AIを活用して補助金申請書のテキストを生成する
        
        Args:
            subsidy_info: 補助金の情報を含む辞書
            business_description: ビジネスの簡単な説明
            
        Returns:
            AI拡張された申請書テキスト
        """
        # 基本的な申請書テンプレートを生成
        base_template = self.generate_application_text(subsidy_info)
        
        try:
            # AIサービスから内容を取得 (非同期関数を適切にawaitする)
            ai_content = await request_ai_content(subsidy_info, business_description)
            
            # テンプレートを拡張
            enhanced_template = base_template.replace(
                "■申請理由：\n[ここに補助金申請の具体的な理由を記入してください。例：\n・事業の現状と課題\n・補助金を活用した事業計画の概要\n・期待される効果や成果\n・予算計画の概要]",
                f"■申請理由：\n{ai_content.get('application_reason', '情報を生成できませんでした。')}"
            ).replace(
                "■事業計画概要：\n[ここに具体的な事業計画を記入してください。計画の実現可能性、革新性、市場性、社会的意義などを明確に説明すると効果的です。]",
                f"■事業計画概要：\n{ai_content.get('business_plan', '情報を生成できませんでした。')}"
            ).replace(
                "■実施体制：\n[ここに事業実施体制について記入してください。担当者の役割や外部との連携体制などを含めると良いでしょう。]",
                f"■実施体制：\n{ai_content.get('implementation_structure', '情報を生成できませんでした。')}"
            ).replace(
                "■スケジュール：\n[ここに事業の実施スケジュールを記入してください。マイルストーンとなる重要な日程も含めると良いでしょう。]",
                f"■スケジュール：\n{ai_content.get('schedule', '情報を生成できませんでした。')}"
            ).replace(
                "■予算計画：\n[ここに予算計画の詳細を記入してください。各費目ごとの金額と、その積算根拠を明確に示すことが重要です。]",
                f"■予算計画：\n{ai_content.get('budget_plan', '情報を生成できませんでした。')}"
            ).replace(
                "■期待される効果：\n[ここに補助金による事業実施で期待される具体的な効果を記入してください。定量的な指標と定性的な効果の両方を含めると良いでしょう。]",
                f"■期待される効果：\n{ai_content.get('expected_effects', '情報を生成できませんでした。')}"
            )
            
            # 補助金情報から重要キーワードを抽出してテンプレートに追加
            keywords = []
            if subsidy_info.get('target_field'):
                keywords.append(subsidy_info.get('target_field'))
            if subsidy_info.get('target_type'):
                keywords.append(subsidy_info.get('target_type'))
            
            # キーワードがあれば追加
            if keywords:
                enhanced_template += f"\n\n※この申請書は以下のキーワードを考慮して作成されています: {', '.join(keywords)}"
            
            # ヘッダーに生成AIを使用した旨を追加
            enhanced_template += "\n\n※このテンプレートは生成AIによって作成されました。内容を確認し、必要に応じて修正してください。"
            
            return enhanced_template
            
        except Exception as e:
            logger.error(f"Failed to generate AI-enhanced application: {str(e)}")
            
            # エラーメッセージを追加
            error_template = base_template + "\n\n※AI拡張機能は現在利用できません。基本テンプレートをご利用ください。"
            return error_template