import os
import logging
import jsonref
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import OpenApiTool, RunStatus, MessageRole, MessageTextContent
from json.decoder import JSONDecodeError
from typing import Optional

from tools.actions import swagger_spec_tool

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
                instructions=f"""You are a subsidies agent. """,
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
                for data_point in reversed(messages.data):
                    last_message_content = data_point.content[-1]
                    if isinstance(last_message_content, MessageTextContent):
                        if data_point.role == MessageRole.AGENT:
                            self.logger.info(f"Agent response: {last_message_content.text.value}")
                            return {"response": last_message_content.text.value}
                
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