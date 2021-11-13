from pathlib import Path

from tinydb import Query, TinyDB

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent / "data"


# 数据库实际为人类可读的 JSON 文件
db = TinyDB(BASE_DIR / "db.json", ensure_ascii=False, indent=2)
unspent_txs_table = db.table('unspent_transactions')
query = Query()


def save_str_to_file(s: str, name: str) -> None:
    with open(BASE_DIR / name, "w") as f:
        f.write(s)


def read_str_from_file(name: str) -> str:
    with open(BASE_DIR / name) as f:
        return f.read()
