from pathlib import Path


def resolve_project_root(project_arg: str | None, cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    if not project_arg:
        return base
    project_path = Path(project_arg)
    if not project_path.is_absolute():
        project_path = base / project_path
    return project_path.resolve()
