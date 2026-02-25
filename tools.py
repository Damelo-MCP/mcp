import os
import httpx
import utils
from typing import Annotated, Optional
from pydantic import Field
from fastmcp.exceptions import ToolError

# API URL de db_api
API_URL = os.environ.get("DAMELO_API_URL") + "/fenix"


async def list_own_creations(github_handle: str) -> str:
    """
    Lista todas las sesiones creadas por el usuario.

    Args:
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        String formateado con la lista de sesiones
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_URL}/sessions",
            headers=utils.get_api_headers(github_handle)
        )

    if resp.status_code != 200:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    sessions = resp.json()

    if not sessions:
        return "No sessions found."

    lines: list[str] = [f"## Your Sessions ({len(sessions)} found)\n"]

    for s in sessions:
        lines.append(f"### {s.get('title', 'Untitled')}")
        lines.append(f"- **ID:** `{s.get('id', 'N/A')}`")
        if s.get('repo'):
            lines.append(f"- **Repo:** {s['repo']}")
        if s.get('description'):
            lines.append(f"- **Description:** {s['description']}")
        if s.get('report_url'):
            lines.append(f"- **Report:** {s['report_url']}")
        lines.append(f"- **Public:** {'Yes' if s.get('is_public') else 'No'}")
        lines.append(f"- **Created:** {s.get('created_at', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


async def list_user_teams(github_handle: str) -> str:
    """
    Lista todos los equipos donde el usuario es miembro.

    Args:
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        String formateado con la lista de equipos
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_URL}/teams",
            headers=utils.get_api_headers(github_handle)
        )

    if resp.status_code != 200:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    teams = resp.json()

    if not teams:
        return "No teams found. You are not a member of any team yet."

    lines: list[str] = [f"## Your Teams ({len(teams)} found)\n"]

    for t in teams:
        owner = t.get("owner", {})

        lines.append(f"### {t.get('name', 'Unnamed Team')}")
        lines.append(f"- **ID:** `{t.get('id', 'N/A')}`")
        lines.append(f"- **Owner:** @{owner.get('github_handle', 'unknown')}")
        if t.get('description'):
            lines.append(f"- **Description:** {t['description']}")
        lines.append(f"- **Created:** {t.get('created_at', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


async def list_team_sessions(team_id: str, github_handle: str) -> str:
    """
    Lista todas las sesiones compartidas con un equipo específico.

    Args:
        team_id: UUID del equipo
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        String formateado con la lista de sesiones del equipo
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_URL}/teams/{team_id}/sessions",
            headers=utils.get_api_headers(github_handle),
        )

    if resp.status_code == 403:
        raise ToolError("Access denied: you are not a member of this team.")
    if resp.status_code == 404:
        raise ToolError(f"Team '{team_id}' not found.")

    if resp.status_code != 200:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    team_sessions = resp.json()

    if not team_sessions:
        return "No sessions shared with this team yet."

    lines: list[str] = [f"## Team Sessions ({len(team_sessions)} found)\n"]

    for ts in team_sessions:
        s = ts.get("session", {})
        owner = s.get("owner", {})

        lines.append(f"### {s.get('title', 'Untitled')}")
        lines.append(f"- **ID:** `{s.get('id', 'N/A')}`")
        lines.append(f"- **Owner:** @{owner.get('github_handle', 'unknown')}")
        if s.get('repo'):
            lines.append(f"- **Repo:** {s['repo']}")
        if s.get('description'):
            lines.append(f"- **Description:** {s['description']}")
        if s.get('report_url'):
            lines.append(f"- **Report:** {s['report_url']}")
        lines.append(f"- **Shared:** {ts.get('shared_at', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


async def list_repo_sessions(repo: str, github_handle: str) -> str:
    """
    Lista todas las sesiones de un repositorio específico.

    Args:
        repo: Nombre del repositorio en formato 'owner/repo'
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        String formateado con la lista de sesiones del repositorio
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_URL}/sessions/by-repo",
            headers=utils.get_api_headers(github_handle),
            params={"repo": repo},
        )

    if resp.status_code != 200:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    sessions = resp.json()

    if not sessions:
        return f"No sessions found for repository '{repo}'."

    lines: list[str] = [f"## Sessions for {repo} ({len(sessions)} found)\n"]

    for s in sessions:
        owner = s.get("owner", {})

        lines.append(f"### {s.get('title', 'Untitled')}")
        lines.append(f"- **ID:** `{s.get('id', 'N/A')}`")
        lines.append(f"- **Owner:** @{owner.get('github_handle', 'unknown')}")
        if s.get('description'):
            lines.append(f"- **Description:** {s['description']}")
        if s.get('report_url'):
            lines.append(f"- **Report:** {s['report_url']}")
        if s.get('metadata', {}).get('git_branch'):
            lines.append(f"- **Branch:** {s['metadata']['git_branch']}")
        lines.append(f"- **Created:** {s.get('created_at', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


async def import_session(session_id: str, github_handle: str) -> str:
    """
    Importa una sesión por su ID, retorna descripción y datos completos de la sesión.

    Args:
        session_id: UUID de la sesión a importar
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        String formateado con los datos de la sesión
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_URL}/sessions/{session_id}",
            headers=utils.get_api_headers(github_handle),
        )

    if resp.status_code == 403:
        raise ToolError("Access denied: you don't have access to this session.")
    if resp.status_code == 404:
        raise ToolError(f"Session '{session_id}' not found.")

    if resp.status_code != 200:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    data = resp.json()

    lines: list[str] = []
    lines.append(f"## {data.get('title', 'Untitled')}")
    if data.get('description'):
        lines.append(f"**Description:** {data['description']}")
    if data.get('report_url'):
        lines.append(f"**Report URL:** {data['report_url']}")
    lines.append(f"\n### Session Data\n")
    lines.append(data.get("session_data", ""))

    return "\n".join(lines)


async def share_session_with_team(
    session_id: str,
    team_id: str,
    github_handle: str
) -> str:
    """
    Comparte una sesión existente con un equipo.

    Args:
        session_id: UUID de la sesión a compartir
        team_id: UUID del equipo con el que compartir
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        String con el resultado de la operación
    """
    payload = {"session_id": session_id}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_URL}/teams/{team_id}/sessions",
            headers=utils.get_api_headers(github_handle),
            json=payload,
        )

    if resp.status_code == 400:
        detail = resp.json().get("detail", "Bad request")
        if "already shared" in detail.lower():
            raise ToolError(f"Session is already shared with this team.")
        raise ToolError(f"Could not share session: {detail}")

    if resp.status_code == 403:
        detail = resp.json().get("detail", "Access denied")
        raise ToolError(f"Access denied: {detail}")

    if resp.status_code == 404:
        detail = resp.json().get("detail", "Not found")
        raise ToolError(f"Not found: {detail}")

    if resp.status_code != 201:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    data = resp.json()

    return (
        f"✅ Session shared successfully!\n\n"
        f"**Session ID:** `{data.get('session_id', session_id)}`\n"
        f"**Team ID:** `{data.get('team_id', team_id)}`\n"
        f"**Message:** {data.get('message', 'Session shared with team')}"
    )


async def update_session(
    session_id: str,
    session_data: str,
    github_handle: str,
) -> str:
    """
    Actualiza el contenido (session_data) de una sesión existente.

    Args:
        session_id: UUID de la sesión a modificar
        session_data: Nuevo contenido HTML de la sesión
        github_handle: El handle de GitHub del usuario autenticado

    Returns:
        String con el resultado de la operación
    """
    payload = {"session_data": session_data}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.patch(
            f"{API_URL}/sessions/{session_id}",
            headers=utils.get_api_headers(github_handle),
            json=payload,
        )

    if resp.status_code == 403:
        raise ToolError("Access denied: only the session owner can update it.")
    if resp.status_code == 404:
        raise ToolError(f"Session '{session_id}' not found.")

    if resp.status_code != 200:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    data = resp.json()

    return (
        f"Session updated successfully!\n\n"
        f"**ID:** `{data.get('id', session_id)}`\n"
        f"**Title:** {data.get('title', 'N/A')}\n"
        f"**Updated:** {data.get('updated_at', 'N/A')}"
    )


async def export_session(
    title: str,
    description: str,
    session_data: str,
    github_handle: str,
    repo: Optional[str] = None,
    topic: Optional[str] = None,
) -> str:
    """
    Exporta y guarda la sesión actual.

    Args:
        title: Título de la sesión
        description: Breve descripción de lo que cubre la sesión
        session_data: String formateado en HTML con el contenido completo de la sesión
        github_handle: El handle de GitHub del usuario autenticado
        repo: Repositorio en formato 'owner/repo' (opcional)
        topic: Si se proporciona, solo incluir las partes relacionadas con este tema (opcional)

    Returns:
        String con el resultado de la exportación
    """
    payload: dict = {
        "title": title,
        "description": description,
        "session_data": session_data,
    }
    if repo is not None:
        payload["repo"] = repo

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_URL}/sessions",
            headers=utils.get_api_headers(github_handle),
            json=payload,
        )

    if resp.status_code == 400:
        detail = resp.json().get("detail", "Bad request")
        raise ToolError(f"Could not export session: {detail}")

    if resp.status_code != 201:
        detail = resp.json().get("detail") if resp.status_code >= 400 else None
        utils.handle_api_error(resp.status_code, detail)

    data = resp.json()

    result = [
        "Session exported successfully!",
        f"**ID:** `{data.get('id', 'unknown')}`",
        f"**Title:** {data.get('title', title)}"
    ]

    if data.get('report_url'):
        result.append(f"**Report:** {data['report_url']}")

    return "\n".join(result)
