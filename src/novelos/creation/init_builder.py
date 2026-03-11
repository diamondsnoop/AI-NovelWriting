from novelos.foundation.io import write_text
from novelos.memory.store import ProjectPaths


def create_project_files(paths: ProjectPaths, title: str) -> None:
    write_text(paths.root / "README.md", f"# {title}\n")
    write_text(paths.outlines_dir / "master_outline.md", "# 总纲\n\n待补充。\n")
