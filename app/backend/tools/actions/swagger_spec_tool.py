from azure.ai.projects.models import OpenApiTool, OpenApiAnonymousAuthDetails

def create_subsidies_tool(openapi_spec) -> OpenApiTool:
    auth = OpenApiAnonymousAuthDetails()
    return OpenApiTool(
        name="subsidies_api",
        description="API for accessing subsidy information",
        spec=openapi_spec,
        auth=auth
    )