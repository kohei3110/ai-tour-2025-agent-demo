import os
import time
import json
import re
from typing import Any, Callable, Set
from urllib.parse import parse_qs, unquote, urlparse
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Agent, AgentThread, BingGroundingTool, ConnectionProperties, RequiredFunctionToolCall, ToolOutput, ToolSet, RunStatus, MessageRole, MessageTextContent, OpenApiTool

from tools.actions.swagger_spec_tool import create_subsidies_tool
from tools.knowledge.bing_grounding_tool import create_bing_grounding_tool

class AssistantManagerService:
    def __init__(self, project_client: AIProjectClient):
        self.project_client = project_client
        self.sources = []

    def create_web_ai_agent_thread(self):

        toolset: ToolSet = ToolSet()

        bing_grounding_connection: ConnectionProperties = self.project_client.connections.get(
            connection_name="bing_search"
        )
        bing_grounding_tool: BingGroundingTool = create_bing_grounding_tool(connection_id=bing_grounding_connection.id)

        toolset.add(bing_grounding_tool)

        thread = self.project_client.agents.create_thread()
        agent: Agent = self.project_client.agents.create_agent(
            model="gpt-35-turbo",
            name="Assistant Manager",
            instructions="""
            あなたは最新情報検索を支援するためのアシスタントです。
            あなたは以下の業務を遂行します。
            - 入力されたキーワードをもとに、最新情報を検索します。最新情報を取得するために Bing Grounding を使用します。

            #制約事項
            - ユーザーからのメッセージは日本語で入力されます
            - ユーザーからのメッセージから忠実に情報を抽出し、それに基づいて応答を生成します。
            - ユーザーからのメッセージに勝手に情報を追加したり、不要な改行文字 \n を追加してはいけません
            """,
            toolset=toolset,
            headers={"x-ms-enable-preview": "true"},
        )
        print(f"Created agent: {agent}")
        return agent, thread
    

    def create_subsidies_agent_thread(self):
        toolset: ToolSet = ToolSet()

        # Load the OpenAPI spec from the JSON file
        swagger_file_path = os.path.join(os.path.dirname(__file__), "..", "tools", "actions", "specs", "swagger_subsidies.json")
        with open(swagger_file_path, "r", encoding="utf-8") as file:
            subsidies_swagger_spec = json.load(file)

        subsidies_tool: OpenApiTool = create_subsidies_tool(subsidies_swagger_spec)
        toolset.add(subsidies_tool)

        thread = self.project_client.agents.create_thread()
        agent: Agent = self.project_client.agents.create_agent(
            model="gpt-35-turbo",
            name="Assistant Manager",
            instructions="""
            あなたは補助金情報検索を支援するためのアシスタントです。
            あなたは以下の業務を遂行します。
            - 入力されたキーワードをもとに、補助金情報を検索します。補助金情報を取得するために OpenAPI 仕様を使用します。

            #制約事項
            - ユーザーからのメッセージは日本語で入力されます
            - ユーザーからのメッセージから忠実に情報を抽出し、それに基づいて応答を生成します。
            - ユーザーからのメッセージに勝手に情報を追加したり、不要な改行文字 \n を追加してはいけません
            """,
            toolset=toolset,
            headers={"x-ms-enable-preview": "true"},
        )
        print(f"Created agent: {agent}")
        return agent, thread
    

    def create_and_send_message(self, user_message: str, agent: Agent, thread: AgentThread):
        self.project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=user_message,
        )
        return self.project_client.agents.create_run(thread_id=thread.id, assistant_id=agent.id)
    
    def execute_tool_calls(self, tool_calls):
        tool_outputs = []
        for tool_call in tool_calls:
            if isinstance(tool_call, RequiredFunctionToolCall):
                try:
                    print(f"Executing tool call: {tool_call}")
                    output = tool_call.execute()
                    response = {"answer": output, "success": True}
                    
                    # Bing Grounding ツールの場合、出典情報を取得
                    tool_info = json.loads(tool_call.json())
                    if "arguments" in tool_info and "query" in tool_info["arguments"]:
                        if "sources" in output:
                            self.sources = output.get("sources", [])
                            print(f"Sources found: {self.sources}")
                    
                    tool_outputs.append(
                        ToolOutput(
                            tool_call_id=tool_call.id,
                            output=json.dumps(response, ensure_ascii=False),
                        )
                    )
                except Exception as e:
                    print(f"Error executing tool_call {tool_call.id}: {e}")
        return tool_outputs

    def get_assistant_responses(self, project_client: AIProjectClient, run, thread: AgentThread):
        agent_messages = self.project_client.agents.list_messages(thread_id=thread.id)
        run_steps = project_client.agents.list_run_steps(run_id=run.id, thread_id=thread.id)
        run_steps_data = run_steps['data']
        print(f"Run steps: {run_steps_data}")

        assistant_messages = []
        url_citations = []
        query = ''

        for data_point in reversed(agent_messages.data):
            last_message_content = data_point.content[-1]
            if not isinstance(last_message_content, MessageTextContent):
                continue

            if data_point.role != MessageRole.AGENT:
                continue

            assistant_messages.append(last_message_content.text.value)

            for annotation in last_message_content.text.annotations:
                if annotation.type != 'url_citation':
                    continue

                url = annotation.get("url_citation", {}).get("url")
                if url:
                    url_citations.append(url)

        # Extract 'q' parameter from requesturl in run steps
        for step in run_steps_data:
            if step['type'] != 'tool_calls':
                continue
                
            for tool_call in step['step_details']['tool_calls']:
                if 'bing_grounding' not in tool_call:
                    continue
                    
                request_url = tool_call['bing_grounding']['requesturl']
                parsed_url = urlparse(request_url)
                query_params = parse_qs(parsed_url.query)
                
                if 'q' in query_params:
                    # URLデコードして検索クエリを取得
                    query = unquote(query_params['q'][0])
                    break  # クエリを見つけたらループを終了
                    
            # クエリが見つかったら外側のループも終了
            if query:
                break
                                        
        return assistant_messages, url_citations, query

    def web_ai_agent(self, user_message: str) -> dict:
        self.sources = []  # 毎回リセット
        agent, thread = self.create_web_ai_agent_thread()
        run = self.create_and_send_message(user_message, agent, thread)

        while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION]:
            time.sleep(1)
            run = self.project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

            if run.status == RunStatus.REQUIRES_ACTION:
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                if not tool_calls:
                    print("No tool calls provided - cancelling run")
                    self.project_client.agents.cancel_run(thread_id=thread.id, run_id=run.id)
                    break

                tool_outputs = self.execute_tool_calls(tool_calls)

                print(f"Tool outputs: {tool_outputs}")
                if tool_outputs:
                    self.project_client.agents.submit_tool_outputs_to_run(
                        thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                    )
                else:
                    print("No tool outputs to submit - cancelling run")
                    self.project_client.agents.cancel_run(thread_id=thread.id, run_id=run.id)
                    break

        print(f"Run completed with status: {run.status}")

        assistant_messages, url_citations, query = self.get_assistant_responses(self.project_client, run, thread)
        print(f"Assistant messages: {assistant_messages}")
        
        return {
            "response": assistant_messages,
            "sources": url_citations,
            "query": query
        }
    
    def subsidies_ai_agent(self, user_message: str) -> dict:
        agent, thread = self.create_subsidies_agent_thread()
        run = self.create_and_send_message(user_message, agent, thread)

        while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION]:
            time.sleep(1)
            run = self.project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

            if run.status == RunStatus.REQUIRES_ACTION:
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                if not tool_calls:
                    print("No tool calls provided - cancelling run")
                    self.project_client.agents.cancel_run(thread_id=thread.id, run_id=run.id)
                    break

                tool_outputs = self.execute_tool_calls(tool_calls)

                print(f"Tool outputs: {tool_outputs}")
                if tool_outputs:
                    self.project_client.agents.submit_tool_outputs_to_run(
                        thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                    )
                else:
                    print("No tool outputs to submit - cancelling run")
                    self.project_client.agents.cancel_run(thread_id=thread.id, run_id=run.id)
                    break

        print(f"Run completed with status: {run.status}")

        assistant_messages, url_citations, query = self.get_assistant_responses(self.project_client, run, thread)
        print(f"Assistant messages: {assistant_messages}")
        
        return {
            "response": assistant_messages,
            "sources": url_citations,
            "query": query
        }