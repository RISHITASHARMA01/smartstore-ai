from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

if not db.query(User).filter(User.email == "admin@smartstore.com").first():
    admin = User(
        email="admin@smartstore.com",
        password=pwd.hash("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("Admin user created")

if not db.query(User).filter(User.email == "staff@smartstore.com").first():
    staff = User(
        email="staff@smartstore.com",
        password=pwd.hash("staff123"),
        role="staff",
        is_active=True,
    )
    db.add(staff)
    db.commit()
    print("Staff user created")

db.close()
print("Seed complete")
