from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class MessageRequest(BaseModel):
    message: str

class ApplicationFormRequest(BaseModel):
    """
    補助金申請書テンプレート生成リクエストモデル
    """
    subsidy_info: Dict[str, Any] = Field(
        ..., 
        description="補助金の情報を含む辞書。title, acceptance_start_datetime, acceptance_end_datetime, target_area_search, subsidy_max_limit, target_number_of_employees などの情報"
    )
    business_description: Optional[str] = Field(
        None,
        description="AI拡張テンプレートを生成する場合のビジネスの説明文。例: 'IT企業向けクラウドサービス開発'"
    )

class PromptRequest(BaseModel):
    """
    AIにプロンプトを送信してメッセージを生成するためのリクエストモデル
    """
    prompt: str = Field(
        ...,
        description="AIに送信するプロンプト"
    )