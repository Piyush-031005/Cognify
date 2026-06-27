import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

print("Upgrading DB schema...")
database.upgrade_database_schema()
print("Done.")
