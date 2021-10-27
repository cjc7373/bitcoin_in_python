from tinydb import TinyDB, Query
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# The db file is human readable.
db = TinyDB(BASE_DIR / 'db.json', ensure_ascii=False, indent=2)
query = Query()
