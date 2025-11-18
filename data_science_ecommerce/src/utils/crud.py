# import json
# import pandas as pd
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent
# DATA_DIR = BASE_DIR / "data"
# JSON_RECORD_PATH = DATA_DIR / "jsonfilerecord.json"

# def build_folder_structure(directory: Path):
#     record = {
#         "file": [],
#         "folder_name": directory.name,
#         "folder": {}
#     }
#     for item in directory.iterdir():
#         if item.is_file() and item.suffix == ".csv":
#             record["file"].append(item.name)
#         elif item.is_dir():
#             record["folder"][item.name] = build_folder_structure(item)
#     return record

# def generate_json_record():
#     structure = build_folder_structure(DATA_DIR)
#     with open(JSON_RECORD_PATH, "w", encoding="utf-8") as f:
#         json.dump(structure, f, indent=4, ensure_ascii=False)
#     return structure

# class CSVCrud:
#     def __init__(self, base_dir=DATA_DIR):
#         self.base_dir = base_dir

#     def _resolve_path(self, folder_path: str, file_name: str):
#         folder = self.base_dir / folder_path
#         folder.mkdir(parents=True, exist_ok=True)
#         return folder / file_name

#     def create_csv(self, folder_path: str, file_name: str, df: pd.DataFrame):
#         path = self._resolve_path(folder_path, file_name)
#         df.to_csv(path, index=False)
#         generate_json_record()
#         return path

#     def read_csv(self, folder_path: str, file_name: str):
#         path = self._resolve_path(folder_path, file_name)
#         return pd.read_csv(path)

#     def update_csv(self, folder_path: str, file_name: str, df: pd.DataFrame):
#         path = self._resolve_path(folder_path, file_name)
#         df.to_csv(path, index=False)
#         return path

#     def delete_csv(self, folder_path: str, file_name: str):
#         path = self._resolve_path(folder_path, file_name)
#         if path.exists():
#             path.unlink()
#             generate_json_record()
#             return True
#         return False
