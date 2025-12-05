"""Manual API testing script to verify all endpoints work correctly."""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Print formatted response."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))

# Test 1: Register a user
print("\n🧪 TEST 1: Register User (POST /users/register)")
response = requests.post(
    f"{BASE_URL}/users/register",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
)
print_response("Register User", response)
assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert "username" in response.json()
assert response.json()["username"] == "testuser"
print("✅ PASS: User registered successfully")

# Test 2: Login to get token
print("\n🧪 TEST 2: Login User (POST /users/login)")
response = requests.post(
    f"{BASE_URL}/users/login",
    json={
        "username": "testuser",
        "password": "password123"
    }
)
print_response("Login User", response)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert "access_token" in response.json()
assert "user" in response.json()
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ PASS: User logged in, token received")

# Test 3: Get current user
print("\n🧪 TEST 3: Get Current User (GET /users/me)")
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
print_response("Get Current User", response)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert response.json()["username"] == "testuser"
print("✅ PASS: Current user retrieved")

# Test 4: Create calculation (Add)
print("\n🧪 TEST 4: Add Calculation (POST /calculations)")
response = requests.post(
    f"{BASE_URL}/calculations",
    headers=headers,
    json={
        "a": 10.5,
        "b": 5.2,
        "type": "add"
    }
)
print_response("Add Calculation", response)
assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert response.json()["result"] == 15.7
calc_id = response.json()["id"]
print("✅ PASS: Calculation created with correct result")

# Test 5: Browse calculations
print("\n🧪 TEST 5: Browse Calculations (GET /calculations)")
response = requests.get(f"{BASE_URL}/calculations", headers=headers)
print_response("Browse Calculations", response)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert len(response.json()) > 0
print("✅ PASS: Calculations list retrieved")

# Test 6: Read specific calculation
print("\n🧪 TEST 6: Read Calculation (GET /calculations/{id})")
response = requests.get(f"{BASE_URL}/calculations/{calc_id}", headers=headers)
print_response("Read Calculation", response)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert response.json()["id"] == calc_id
print("✅ PASS: Specific calculation retrieved")

# Test 7: Create more calculations
print("\n🧪 TEST 7: Create Multiple Calculations")
operations = [
    {"a": 20, "b": 4, "type": "subtract", "expected": 16},
    {"a": 6, "b": 7, "type": "multiply", "expected": 42},
    {"a": 15, "b": 3, "type": "divide", "expected": 5}
]

for op in operations:
    response = requests.post(
        f"{BASE_URL}/calculations",
        headers=headers,
        json={"a": op["a"], "b": op["b"], "type": op["type"]}
    )
    assert response.status_code == 201
    assert response.json()["result"] == op["expected"]
    print(f"  ✓ {op['a']} {op['type']} {op['b']} = {response.json()['result']}")

print("✅ PASS: All calculation types work correctly")

# Test 8: Edit calculation (PUT)
print("\n🧪 TEST 8: Edit Calculation (PUT /calculations/{id})")
response = requests.put(
    f"{BASE_URL}/calculations/{calc_id}",
    headers=headers,
    json={"a": 30, "b": 10, "type": "multiply"}
)
print_response("Edit Calculation (PUT)", response)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert response.json()["result"] == 300
print("✅ PASS: Calculation updated successfully")

# Test 9: Edit calculation (PATCH)
print("\n🧪 TEST 9: Partial Edit (PATCH /calculations/{id})")
response = requests.patch(
    f"{BASE_URL}/calculations/{calc_id}",
    headers=headers,
    json={"b": 5}
)
print_response("Edit Calculation (PATCH)", response)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert response.json()["result"] == 150  # 30 * 5
print("✅ PASS: Partial update works correctly")

# Test 10: Delete calculation
print("\n🧪 TEST 10: Delete Calculation (DELETE /calculations/{id})")
response = requests.delete(f"{BASE_URL}/calculations/{calc_id}", headers=headers)
print_response("Delete Calculation", response)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert "deleted successfully" in response.json()["message"]
print("✅ PASS: Calculation deleted successfully")

# Test 11: Verify deletion
print("\n🧪 TEST 11: Verify Deletion")
response = requests.get(f"{BASE_URL}/calculations/{calc_id}", headers=headers)
assert response.status_code == 404, f"Expected 404, got {response.status_code}"
print("✅ PASS: Deleted calculation no longer accessible")

# Test 12: Test error handling (division by zero)
print("\n🧪 TEST 12: Error Handling - Division by Zero")
response = requests.post(
    f"{BASE_URL}/calculations",
    headers=headers,
    json={"a": 10, "b": 0, "type": "divide"}
)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 422, f"Expected 422, got {response.status_code}"
print("✅ PASS: Division by zero properly rejected")

# Test 13: Test authentication requirement
print("\n🧪 TEST 13: Authentication Requirement")
response = requests.get(f"{BASE_URL}/calculations")
assert response.status_code == 403, f"Expected 403, got {response.status_code}"
print("✅ PASS: Endpoints properly require authentication")

print("\n" + "="*70)
print("🎉 ALL TESTS PASSED!")
print("="*70)
print("\n✅ Summary:")
print("  - User registration works")
print("  - User login returns JWT token")
print("  - Protected endpoints require authentication")
print("  - All BREAD operations function correctly")
print("  - All calculation types (add, subtract, multiply, divide) work")
print("  - Partial updates (PATCH) work")
print("  - Error handling (division by zero) works")
print("  - Data validation works")
print("\n📚 API Documentation available at:")
print(f"  - Swagger UI: {BASE_URL}/docs")
print(f"  - ReDoc: {BASE_URL}/redoc")
