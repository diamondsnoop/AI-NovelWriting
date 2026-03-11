from pathlib import Path

from novelos.presentation.dashboard import build_dashboard_view
from novelos.presentation.status_report import build_status_report
from novelos.query.service import query_project


def run_query(project_root: Path, query_type: str) -> dict:
    if query_type == "status_report":
        return build_status_report(project_root)
    if query_type == "dashboard":
        return build_dashboard_view(project_root)
    return query_project(project_root=project_root, query_type=query_type)
