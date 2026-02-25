import os
import httpx
import utils
import tools

from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_access_token
from key_value.aio.stores.dynamodb import DynamoDBStore
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get("DAMELO_API_URL") + "/fenix"

class UserValidationMiddleware(Middleware):
    """
    Middleware que valida/crea el usuario en db_api después de la autenticación OAuth.
    Extrae el github_handle del token de GitHub y asegura que el usuario existe en db_api.
    """
    async def on_initialize(self, context: MiddlewareContext, call_next):

        token = get_access_token()
        github_handle = token.claims.get("login")

        if not github_handle:
            raise ToolError("Could not extract GitHub handle from OAuth token")

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{API_URL}/auth/validate-or-create",
                    headers=utils.get_api_headers(github_handle),
                    json={
                        "email": token.claims.get("email"),
                        "display_name": token.claims.get("name")
                    }
                )

                if resp.status_code not in [200, 201]:
                    print(f"Warning: Could not validate/create user in db_api: {resp.status_code}")
                else:
                    user_data = resp.json()
                    existed = user_data.get("existed", False)
                    if existed:
                        print(f"User @{github_handle} validated in db_api")
                    else:
                        print(f"User @{github_handle} created in db_api")

            except Exception as e:
                print(f"Error validating user in db_api: {e}")

        response = await call_next(context)
        return response