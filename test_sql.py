import sqlite3

# Test SQL syntax
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Test 1 - Current syntax (should fail)
try:
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", ('test', 'test@test.com', 'password'))
    print("✅ Current syntax works")
except Exception as e:
    print(f"❌ Current syntax failed: {e}")

# Test 2 - Fixed syntax (should work)
try:
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", ('test', 'test@test.com', 'password'))
    print("✅ Fixed syntax works")
except Exception as e:
    print(f"❌ Fixed syntax failed: {e}")
