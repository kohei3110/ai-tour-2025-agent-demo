import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from services.assistant_manager_service import AssistantManagerService


load_dotenv()

app: FastAPI = FastAPI(
    title="API Sample for Agent SDK",
    description="API for Agent SDK",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ローカル開発用: 本番環境では特定のオリジンを指定する
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのHTTPヘッダーを許可
)

project_client: AIProjectClient = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
)

assistant_manager_service = AssistantManagerService(project_client)

import controller
app.include_router(controller.router)