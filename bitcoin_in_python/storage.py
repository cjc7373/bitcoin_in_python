import os
from pathlib import Path
from typing import TYPE_CHECKING

from sqlitedict import SqliteDict

if TYPE_CHECKING:
    from block import Block
    from transaction import Transaction

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent / "data"
BASE_DIR = Path(os.getcwd())

# 数据库同时也是一个全局状态, 可以在各处被使用
db_file = BASE_DIR / 'db.sqlite3'
chain_db: dict[str, 'Block'] = SqliteDict(db_file, tablename='blockchain', autocommit=True)
misc_db: dict[str, str] = SqliteDict(db_file, tablename='misc', autocommit=True)
unspent_txs_db: dict[str, 'Transaction'] = SqliteDict(
    db_file, tablename='unspent_txs', autocommit=True
)


def save_str_to_file(s: str, name: str) -> None:
    with open(BASE_DIR / name, "w") as f:
        f.write(s)


def read_str_from_file(name: str) -> str:
    with open(BASE_DIR / name) as f:
        return f.read()
