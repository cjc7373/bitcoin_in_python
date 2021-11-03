from tinydb import TinyDB, Query
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# 数据库实际为人类可读的 JSON 文件
db = TinyDB(BASE_DIR / "db.json", ensure_ascii=False, indent=2)
query = Query()
