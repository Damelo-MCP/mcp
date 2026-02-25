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
from middleware import UserValidationMiddleware

load_dotenv()

BASE_URL = os.environ.get("BASE_URL")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENTE_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENTE_SECRET")
AMAZON_ACCESS_ID = os.environ.get("AMAZON_ACCESS_ID")
AMAZON_SECRET_ID = os.environ.get("AMAZON_SECRET_ID")


auth = GitHubProvider(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    base_url=BASE_URL,
    redirect_path="/auth/github/callback",
    client_storage=DynamoDBStore(
        table_name="llaves-damelo",
        region_name="us-east-1",
        aws_access_key_id=AMAZON_ACCESS_ID,
        aws_secret_access_key=AMAZON_SECRET_ID
    )
)

# Crear instancia de FastMCP
mcp = FastMCP(
    name="Damelo",
    instructions=(
        """Dámelo lets you share and manage AI assistant sessions (Claude Code, Cursor, etc.) with your teams.

        Export and import all your sessions so nothing is missed. You can:
        - Export sessions with detailed summaries
        - List your own sessions
        - Browse sessions shared with your teams
        - Import sessions from teammates
        - Search sessions by repository

        All sessions are stored securely and can be shared with your team members.

        **CRITICAL: All session_data MUST be properly formatted HTML**

        The session_data parameter accepts ONLY valid HTML format. This will be saved as an .html file.

        **Required HTML formatting:**
        - Use proper HTML structure with <!DOCTYPE html>, <html>, <head>, and <body> tags
        - Use semantic HTML5 tags: <header>, <main>, <section>, <article>, <footer>
        - Use heading tags (<h1>, <h2>, <h3>, etc.) for document structure
        - Use <pre><code> blocks for code snippets, with class attribute for syntax highlighting (e.g., <code class="language-python">)
        - Use <ul>/<ol> and <li> for lists
        - Use <strong> and <em> for emphasis
        - Use <a href="url"> for links
        - Include proper CSS styling in <style> tags or inline for better presentation
        - Ensure all tags are properly closed and nested
        """
    ),
    auth=auth
)

mcp.add_middleware(UserValidationMiddleware())

# ============================================
# TOOL REGISTRATION
# ============================================

@mcp.tool(
    name="list_own_creations",
    description="List all sessions created by the user",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def list_own_creations_tool() -> str:
    """Lista todas las sesiones creadas por el usuario autenticado."""
    github_handle = utils.get_github_handle()
    return await tools.list_own_creations(github_handle)


@mcp.tool(
    name="list_user_teams",
    description="List all teams where the user is a member",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def list_user_teams_tool() -> str:
    """Lista todos los equipos donde el usuario es miembro."""
    github_handle = utils.get_github_handle()
    return await tools.list_user_teams(github_handle)


@mcp.tool(
    name="list_team_sessions",
    description="List all sessions shared with a specific team",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def list_team_sessions_tool(
    team_id: Annotated[str, Field(description="UUID of the team")]
) -> str:
    """Lista todas las sesiones compartidas con un equipo específico."""
    github_handle = utils.get_github_handle()
    return await tools.list_team_sessions(team_id, github_handle)


@mcp.tool(
    name="list_repo_sessions",
    description="List all sessions of a specific repository",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def list_repo_sessions_tool(
    repo: Annotated[str, Field(description="Repository name in 'owner/repo' format")]
) -> str:
    """Lista todas las sesiones de un repositorio específico."""
    github_handle = utils.get_github_handle()
    return await tools.list_repo_sessions(repo, github_handle)


@mcp.tool(
    name="import_session",
    description="Import a session by its ID, returns description and full session data",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def import_session_tool(
    session_id: Annotated[str, Field(description="UUID of the session to import")]
) -> str:
    """Importa una sesión por su ID."""
    github_handle = utils.get_github_handle()
    return await tools.import_session(session_id, github_handle)


@mcp.tool(
    name="share_session_with_team",
    description="Share an existing session with a team",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def share_session_with_team_tool(
    session_id: Annotated[str, Field(description="UUID of the session to share")],
    team_id: Annotated[str, Field(description="UUID of the team to share with")]
) -> str:
    """Comparte una sesión existente con un equipo."""
    github_handle = utils.get_github_handle()
    return await tools.share_session_with_team(session_id, team_id, github_handle)


@mcp.tool(
    name="update_session",
    description=(
        "Update the content (session_data) of an existing session. "
        "Only the session owner can update it. "
        "CRITICAL: session_data MUST be a PROPERLY FORMATTED HTML string with complete HTML structure "
        "including <!DOCTYPE html>, <html>, <head>, and <body> tags."
    ),
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def update_session_tool(
    session_id: Annotated[str, Field(description="UUID of the session to update")],
    session_data: Annotated[str, Field(description="New HTML-formatted content for the session")],
) -> str:
    """Actualiza el contenido de una sesión existente."""
    github_handle = utils.get_github_handle()
    return await tools.update_session(session_id, session_data, github_handle)


@mcp.tool(
    name="export_session",
    description=(
        "Export and save the current session. "
        "If 'topic' is provided, only include conversation and changes relevant to that topic (thematic export). "
        "If 'topic' is omitted, export the entire session. "
        "CRITICAL: session_data MUST be a PROPERLY FORMATTED HTML string with complete HTML structure "
        "including <!DOCTYPE html>, <html>, <head>, and <body> tags. Use semantic HTML5 tags (<header>, <main>, <section>, <article>), "
        "heading tags (<h1>, <h2>, <h3>), <pre><code class='language-*'> for code blocks, and proper CSS styling. "
        "This will be saved as an .html file. "
        "The summary must comprehensively represent the conversation and insights, detailed enough to understand without reading the full conversation. "
        "IMPORTANT: Run 'git remote -v' to get the repository origin URL and include it in the 'repo' parameter. "
        "Returns a report_url link to the generated .html file."
    ),
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": True,
    },
    task=True
)
async def export_session_tool(
    title: Annotated[str, Field(description="Title for the session")],
    description: Annotated[str, Field(description="Short description of what the session covers")],
    session_data: Annotated[str, Field(description="HTML-formatted string with the complete session content including proper HTML structure")],
    repo: Annotated[Optional[str], Field(description="Repository origin (.git url) run git remote -v to check if there is one")] = None,
    topic: Annotated[Optional[str], Field(
        description="If set, only the parts of the session related to this topic should be included in session_data"
    )] = None,
) -> str:
    """Exporta y guarda la sesión actual."""
    github_handle = utils.get_github_handle()
    return await tools.export_session(title, description, session_data, github_handle, repo, topic)


# ============================================
# ENTRYPOINT
# ============================================

app = mcp.http_app()