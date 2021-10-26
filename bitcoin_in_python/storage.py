from tinydb import TinyDB, Query

# The db file is human readable.
db = TinyDB('../db.json', ensure_ascii=False, indent=2)
query = Query()
