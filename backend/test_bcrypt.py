from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test various passwords
test_passwords = [
    "test123",
    "testpassword123",
    "a",
    "12345678",
    None,
    "",
]

for pw in test_passwords:
    try:
        print(f"Testing password: {repr(pw)}")
        if pw is not None:
            hashed = pwd_context.hash(pw)
            print(f"  ✓ Success: {hashed[:30]}...")
        else:
            print(f"  Skipping None")
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
    print()
