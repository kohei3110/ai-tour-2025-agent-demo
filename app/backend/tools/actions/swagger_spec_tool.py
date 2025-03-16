from azure.ai.projects.models import OpenApiAnonymousAuthDetails, OpenApiTool


def create_openapi_tool(openapi_spec):
    auth = OpenApiAnonymousAuthDetails()
    openapi_tool = OpenApiTool(
        name="get_subsidies", 
        spec=openapi_spec, 
        description="Search subsidies with conditions", 
        auth=auth
    )
    return openapi_tool