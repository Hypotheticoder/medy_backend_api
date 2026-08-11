from db import SessionLocal
from crud.lab_test import get_inventory_for_lab

db = SessionLocal()
try:
    print(get_inventory_for_lab(db, "LAB-D49B48E3"))
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
