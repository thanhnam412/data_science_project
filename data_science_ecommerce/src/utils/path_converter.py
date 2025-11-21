def path_converter(path: str, root_folder="src") -> "str":
    from pathlib import Path

    current_dir = Path.cwd()
    project_root = current_dir.parent
    result = str(project_root).split(root_folder)[0] + root_folder
    return f"{result}/{path}"
