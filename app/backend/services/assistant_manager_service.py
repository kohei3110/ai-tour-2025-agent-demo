import os
import logging
import jsonref
import re
import json
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import OpenApiTool, RunStatus, MessageRole, MessageTextContent
from json.decoder import JSONDecodeError
from typing import Optional, Dict, Any, List

from tools.actions import swagger_spec_tool
from tools.actions.application_doc_generator_tool import generate_application_text

class AssistantManagerService:
    def __init__(self, project_client: AIProjectClient):
        self.project_client = project_client
        self.logger = logging.getLogger(__name__)

    async def process_openapi_spec(self, request):
        try:
            openapi_spec = self.load_openapi_spec()
            openapi_tool: OpenApiTool = self.create_openapi_tool(openapi_spec)
            agent = self.project_client.agents.create_agent(
                model="gpt-4o-mini",
                name="Subsidies Agent",
                instructions=f"""You are a subsidies agent. When providing information about subsidies, include specific details such as application periods, target areas, subsidy limits, and eligibility requirements when available.""",
                tools=openapi_tool.definitions
            )
            
            thread = self.project_client.agents.create_thread()
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=request.message,
            )
            
            try:
                run = self.project_client.agents.create_and_process_run(
                    thread_id=thread.id, 
                    agent_id=agent.id
                )

                self.logger.info(f"Run status: {run.status}")
                
                if run.status == RunStatus.FAILED:
                    self.logger.error(f"Run failed: {run.last_error}")
                    return {"error": f"Run failed: {run.last_error}"}
                
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                self.logger.info(f"Messages: {messages}")
                
                # 応答メッセージと補助金情報を取得
                response_text = ""
                subsidy_info = None
                
                for data_point in reversed(messages.data):
                    last_message_content = data_point.content[-1]
                    if isinstance(last_message_content, MessageTextContent):
                        if data_point.role == MessageRole.AGENT:
                            response_text = last_message_content.text.value
                            self.logger.info(f"Agent response: {response_text}")
                            
                            # 応答から補助金情報を抽出
                            subsidy_info = self.extract_subsidy_info(response_text)
                            break
                
                if response_text:
                    result = {"response": response_text}
                    
                    # 補助金情報が抽出できた場合は申請書テキストを生成
                    if subsidy_info:
                        application_text = generate_application_text(subsidy_info)
                        result["application_text"] = application_text
                    
                    return result
                
                return {"response": "No response found"}
                
            except JSONDecodeError as e:
                self.logger.error(f"JSON decode error in API response: {str(e)}")
                return {"error": "Invalid response from subsidies API"}
            finally:
                # Clean up resources
                self.project_client.agents.delete_agent(agent.id)
                
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Error processing request: {str(e)}"}

    def extract_subsidy_info(self, text: str) -> Optional[Dict[str, Any]]:
        """
        テキストから補助金情報を抽出する
        
        Args:
            text: 補助金に関するテキスト
            
        Returns:
            抽出された補助金情報の辞書、または抽出できなかった場合はNone
        """
        # 補助金情報を含まない場合は早期リターン
        subsidy_keywords = ['補助金', '助成金', '支援金', '奨励金']
        if not any(keyword in text for keyword in subsidy_keywords):
            return None
            
        try:
            # タイトルの抽出 (最初の行や強調表示された部分を探す)
            title = None
            title_match = re.search(r'\*\*([^*]+補助金[^*]*)\*\*', text) or \
                         re.search(r'^(?:\d+\.\s*)?(.+補助金.+)$', text, re.MULTILINE) or \
                         re.search(r'「([^」]+補助金[^」]+)」', text)
            
            if title_match:
                title = title_match.group(1).strip()
            else:
                # 「〜補助金」のパターンを探す
                title_pattern = re.search(r'([^\n,.、。]+補助金[^\n,.、。]*)', text)
                if title_pattern:
                    title = title_pattern.group(1).strip()
            
            # 情報を格納する辞書
            subsidy_info = {}
            if title:
                subsidy_info["title"] = title
            
            # 対象地域の抽出
            area_match = re.search(r'対象(?:地域|エリア)[:：]?\s*([^\n]+)', text) or \
                        re.search(r'対象[:：]?\s*([^\n]*(?:全国|都道府県|市区町村)[^\n]*)', text)
            if area_match:
                subsidy_info["target_area_search"] = area_match.group(1).strip()
            
            # 補助金上限額の抽出
            amount_match = re.search(r'(?:補助(?:金額|上限|限度額)|上限額)[:：]?\s*([0-9,.，億万千百]+(?:円|万円|億円))', text) or \
                          re.search(r'上限(?:は|：)?\s*([0-9,.，億万千百]+(?:円|万円|億円))', text)
            
            if amount_match:
                amount_str = amount_match.group(1).strip()
                # 文字列から数値への変換
                amount = self._convert_ja_currency_to_int(amount_str)
                if amount:
                    subsidy_info["subsidy_max_limit"] = amount
            
            # 申請期間の抽出
            period_match = re.search(r'(?:申請|募集|応募)期間[:：]?\s*([^\n]+)', text)
            if period_match:
                period_str = period_match.group(1).strip()
                # 開始日と終了日を分離して処理
                dates = self._extract_date_range(period_str)
                if dates and "start" in dates:
                    subsidy_info["acceptance_start_datetime"] = dates["start"]
                if dates and "end" in dates:
                    subsidy_info["acceptance_end_datetime"] = dates["end"]
            
            # 従業員数制限の抽出
            employee_match = re.search(r'(?:従業員|対象企業|対象者)[:：]?\s*([^\n]*\d+名[^\n]*)', text) or \
                            re.search(r'対象[:：]?\s*([^\n]*(?:中小企業|小規模事業者)[^\n]*)', text)
            if employee_match:
                subsidy_info["target_number_of_employees"] = employee_match.group(1).strip()
            
            # 最低限必要な情報があるか確認
            if subsidy_info and ("title" in subsidy_info or "subsidy_max_limit" in subsidy_info):
                return subsidy_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting subsidy info: {str(e)}")
            return None
    
    def _convert_ja_currency_to_int(self, amount_str: str) -> Optional[int]:
        """
        日本語の金額表記を整数に変換する
        
        Args:
            amount_str: 金額の文字列表記（例: "1億5000万円", "3,000万円"）
            
        Returns:
            変換された整数値、または変換できなかった場合はNone
        """
        try:
            # カンマと全角カンマを削除
            amount_str = amount_str.replace(',', '').replace('，', '')
            
            # 単位ごとに分解して計算
            amount = 0
            
            # 億単位の処理
            oku_match = re.search(r'(\d+)億', amount_str)
            if oku_match:
                amount += int(oku_match.group(1)) * 100000000
            
            # 万単位の処理
            man_match = re.search(r'(\d+)万', amount_str)
            if man_match:
                amount += int(man_match.group(1)) * 10000
            
            # 円単位の処理 (万や億がない場合)
            if not oku_match and not man_match:
                yen_match = re.search(r'(\d+)円', amount_str)
                if yen_match:
                    amount += int(yen_match.group(1))
            
            return amount if amount > 0 else None
            
        except Exception:
            return None
    
    def _extract_date_range(self, period_str: str) -> Optional[Dict[str, str]]:
        """
        期間文字列から開始日と終了日を抽出する
        
        Args:
            period_str: 期間を表す文字列（例: "2024年4月1日～2024年5月30日"）
            
        Returns:
            {"start": ISO形式の開始日, "end": ISO形式の終了日}、または抽出できなかった場合はNone
        """
        try:
            # 日付パターンにマッチさせる
            date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
            
            # 開始日と終了日を抽出
            dates = re.findall(date_pattern, period_str)
            
            if len(dates) >= 2:
                start_year, start_month, start_day = dates[0]
                end_year, end_month, end_day = dates[1]
                
                # ISO形式に変換
                start_iso = f"{start_year}-{int(start_month):02d}-{int(start_day):02d}T00:00:00Z"
                end_iso = f"{end_year}-{int(end_month):02d}-{int(end_day):02d}T23:59:59Z"
                
                return {"start": start_iso, "end": end_iso}
            elif len(dates) == 1:
                # 開始日のみの場合
                year, month, day = dates[0]
                date_iso = f"{year}-{int(month):02d}-{int(day):02d}T00:00:00Z"
                
                # 「〜」や「から」の後に日付がある場合は終了日として扱う
                if '～' in period_str or 'から' in period_str or '~' in period_str:
                    return {"end": date_iso}
                else:
                    return {"start": date_iso}
            
            return None
            
        except Exception:
            return None

    def load_openapi_spec(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            spec_path = os.path.join(current_dir, "..", "tools", "actions", "specs", "swagger_subsidies.json")
            with open(spec_path, "r") as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("Empty OpenAPI specification file")
                openapi_spec = jsonref.loads(content)
            return openapi_spec
        except JSONDecodeError as e:
            self.logger.error(f"Failed to parse OpenAPI spec: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load OpenAPI spec: {str(e)}")
            raise

    def create_openapi_tool(self, openapi_spec):
        return swagger_spec_tool.create_subsidies_tool(openapi_spec)