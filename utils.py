import os
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token
from dotenv import load_dotenv

load_dotenv()

MCP_API_KEY = os.environ.get("MCP_API_KEY")

def get_github_handle() -> str:
    """
    Extrae el github_handle del contexto del MCP.
    Este handle fue guardado por el UserValidationMiddleware.
    """
    token = get_access_token()
    github_handle = token.claims.get("login")

    if not github_handle: raise ToolError("GitHub handle not found in session")

    return github_handle

def get_api_headers(github_handle: str) -> dict[str, str]:
    """
    Genera los headers necesarios para autenticar con db_api.

    Args:
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        Dict con los headers X-MCP-API-Key y X-GitHub-Handle
    """
    if not MCP_API_KEY:
        raise ToolError("MCP_API_KEY not configured in environment variables")

    if not github_handle:
        raise ToolError("GitHub handle is required")

    return {
        "X-MCP-API-Key": MCP_API_KEY,
        "X-GitHub-Handle": github_handle,
        "Content-Type": "application/json",
    }


def handle_api_error(status_code: int, detail: str = None) -> None:
    """
    Maneja errores comunes de la API.

    Args:
        status_code: Código de estado HTTP
        detail: Mensaje de error opcional
    """
    if status_code == 401:
        raise ToolError("Authentication failed - Invalid MCP API key")
    elif status_code == 403:
        raise ToolError(f"Access denied: {detail or 'Insufficient permissions'}")
    elif status_code == 404:
        raise ToolError(f"Not found: {detail or 'Resource not found'}")
    elif status_code >= 400:
        raise ToolError(f"API error ({status_code}): {detail or 'Unknown error'}")
