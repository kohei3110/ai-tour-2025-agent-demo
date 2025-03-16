from azure.ai.projects.models import OpenApiAnonymousAuthDetails, OpenApiTool


def create_subsidies_tool(openapi_spec):
    auth = OpenApiAnonymousAuthDetails()
    subsidies_tool = OpenApiTool(
        name="get_subsidies", 
        spec=openapi_spec, 
        description="Search subsidies with conditions", 
        auth=auth
    )
    return subsidies_tool