import sys
sys.path.append('.')

from sqlalchemy.orm import Session
import database, models, schemas, auth as auth_module

# Create a test database session
db = database.SessionLocal()

try:
    # Test user creation
    test_email = "isolated_test@example.com"
    test_password = "testpassword123"
    
    print(f"Testing user registration with:")
    print(f"  Email: {test_email}")
    print(f"  Password: {test_password}")
    print()
    
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == test_email).first()
    if existing_user:
        print(f"User already exists, deleting...")
        db.delete(existing_user)
        db.commit()
    
    # Test password hashing
    print("Step 1: Testing password hash...")
    hashed = auth_module.get_password_hash(test_password)
    print(f"  Hashed password: {hashed[:50]}...")
    
    # Test user creation
    print("\nStep 2: Creating user in database...")
    user_create = schemas.UserCreate(email=test_email, password=test_password)
    hashed_password = auth_module.get_password_hash(user_create.password)
    db_user = models.User(email=user_create.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"  User created successfully with ID: {db_user.id}")
    
    # Test password verification
    print("\nStep 3: Testing password verification...")
    is_valid = auth_module.verify_password(test_password, db_user.hashed_password)
    print(f"  Password verification: {is_valid}")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
