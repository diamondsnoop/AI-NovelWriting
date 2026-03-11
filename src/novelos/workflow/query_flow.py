from pathlib import Path

from novelos.query.service import query_project


def run_query(project_root: Path, query_type: str) -> dict:
    return query_project(project_root=project_root, query_type=query_type)
