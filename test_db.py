from db import SessionLocal
from models.lab_test import LabTest
from models.lab_test_pricing import LabTestPricing

db = SessionLocal()

package = db.query(LabTest).filter(LabTest.is_package == True).first()
if not package:
    print("No packages found")
    exit()

pricing = db.query(LabTestPricing).filter(LabTestPricing.test_id == package.test_id).first()

print(f"Found package: {package.test_name} (ID: {package.test_id})")
print(f"Description: {package.description}")
print(f"Included tests: {package.included_tests}")
print(f"Lab ID: {pricing.lab_id}")
