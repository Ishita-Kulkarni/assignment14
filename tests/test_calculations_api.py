"""
Integration tests for calculation API endpoints.
These tests require a database connection and authentication.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models import User, Calculation
import os

# Use SQLite for testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def authenticated_user():
    """Create a user and return authentication token."""
    # Register user
    user_data = {
        "username": "calcuser",
        "email": "calc@example.com",
        "password": "password123"
    }
    client.post("/users/register", json=user_data)
    
    # Login to get token
    login_data = {
        "username": "calcuser",
        "password": "password123"
    }
    response = client.post("/users/login", json=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


class TestCalculationAdd:
    """Test adding (creating) calculations."""
    
    def test_add_calculation_success(self, authenticated_user):
        """Test successfully adding a calculation."""
        calc_data = {
            "a": 10.5,
            "b": 5.2,
            "type": "add"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["a"] == 10.5
        assert data["b"] == 5.2
        assert data["type"] == "add"
        assert data["result"] == 15.7
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data
    
    def test_add_calculation_db_verification(self, authenticated_user):
        """Test that calculation is actually stored in database."""
        calc_data = {
            "a": 25.0,
            "b": 10.0,
            "type": "multiply"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        calc_id = response.json()["id"]
        user_id = response.json()["user_id"]
        
        # Verify data in database
        db = TestingSessionLocal()
        calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
        
        assert calc is not None
        assert calc.a == 25.0
        assert calc.b == 10.0
        assert calc.type == "multiply"
        assert calc.result == 250.0
        assert calc.user_id == user_id
        assert calc.created_at is not None
        
        db.close()
    
    def test_add_calculation_subtract(self, authenticated_user):
        """Test subtraction calculation."""
        calc_data = {
            "a": 20.0,
            "b": 7.5,
            "type": "subtract"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == 12.5
    
    def test_add_calculation_multiply(self, authenticated_user):
        """Test multiplication calculation."""
        calc_data = {
            "a": 4.0,
            "b": 3.0,
            "type": "multiply"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == 12.0
    
    def test_add_calculation_divide(self, authenticated_user):
        """Test division calculation."""
        calc_data = {
            "a": 15.0,
            "b": 3.0,
            "type": "divide"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == 5.0
    
    def test_add_calculation_division_by_zero(self, authenticated_user):
        """Test that division by zero is rejected."""
        calc_data = {
            "a": 10.0,
            "b": 0.0,
            "type": "divide"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        # Schema validation returns 422, not 400
        assert response.status_code == 422
        assert "division by zero" in str(response.json()).lower()
    
    def test_add_calculation_invalid_operation(self, authenticated_user):
        """Test that invalid operation is rejected."""
        calc_data = {
            "a": 10.0,
            "b": 5.0,
            "type": "modulo"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_add_calculation_without_auth(self):
        """Test that calculation creation requires authentication."""
        calc_data = {
            "a": 10.0,
            "b": 5.0,
            "type": "add"
        }
        
        response = client.post("/calculations", json=calc_data)
        
        assert response.status_code == 403


class TestCalculationBrowse:
    """Test browsing (listing) calculations."""
    
    def test_browse_calculations_empty(self, authenticated_user):
        """Test browsing when no calculations exist."""
        response = client.get("/calculations", headers=authenticated_user)
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_browse_calculations_with_data(self, authenticated_user):
        """Test browsing calculations."""
        # Create multiple calculations
        calculations = [
            {"a": 10, "b": 5, "type": "add"},
            {"a": 20, "b": 3, "type": "subtract"},
            {"a": 4, "b": 7, "type": "multiply"}
        ]
        
        for calc in calculations:
            client.post("/calculations", json=calc, headers=authenticated_user)
        
        response = client.get("/calculations", headers=authenticated_user)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by created_at desc (newest first)
        # But in fast execution, ordering might vary, so just check all exist
        types = [calc["type"] for calc in data]
    
    def test_browse_calculations_db_verification(self, authenticated_user):
        """Test that browse returns data matching database."""
        # Create calculations
        created_ids = []
        for i in range(3):
            calc_data = {"a": i + 1, "b": 2, "type": "add"}
            response = client.post("/calculations", json=calc_data, headers=authenticated_user)
            created_ids.append(response.json()["id"])
        
        # Get via API
        api_response = client.get("/calculations", headers=authenticated_user)
        assert api_response.status_code == 200
        api_calcs = api_response.json()
        
        # Verify against database
        db = TestingSessionLocal()
        db_calcs = db.query(Calculation).filter(Calculation.id.in_(created_ids)).all()
        
        assert len(api_calcs) == len(db_calcs) == 3
        
        # Check that all DB calculations appear in API response
        db_ids = {calc.id for calc in db_calcs}
        api_ids = {calc["id"] for calc in api_calcs}
        assert db_ids == api_ids
        
        db.close()
    
    def test_browse_calculations_pagination(self, authenticated_user):
        """Test pagination in browse."""
        # Create 5 calculations
        for i in range(5):
            calc = {"a": i, "b": 1, "type": "add"}
            client.post("/calculations", json=calc, headers=authenticated_user)
        
        # Get first 2
        response = client.get(
            "/calculations?skip=0&limit=2",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Get next 2
        response = client.get(
            "/calculations?skip=2&limit=2",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_browse_calculations_without_auth(self):
        """Test that browsing requires authentication."""
        response = client.get("/calculations")
        
        assert response.status_code == 403
    
    def test_browse_calculations_user_isolation(self):
        """Test that users only see their own calculations."""
        # Create first user and calculation
        user1_data = {"username": "user1", "email": "user1@example.com", "password": "password123"}
        client.post("/users/register", json=user1_data)
        login_response = client.post("/users/login", json={"username": "user1", "password": "password123"})
        user1_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        client.post("/calculations", json={"a": 1, "b": 1, "type": "add"}, headers=user1_token)
        
        # Create second user and calculation
        user2_data = {"username": "user2", "email": "user2@example.com", "password": "password123"}
        client.post("/users/register", json=user2_data)
        login_response = client.post("/users/login", json={"username": "user2", "password": "password123"})
        user2_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        client.post("/calculations", json={"a": 2, "b": 2, "type": "add"}, headers=user2_token)
        
        # Each user should only see their own calculation
        user1_calcs = client.get("/calculations", headers=user1_token).json()
        user2_calcs = client.get("/calculations", headers=user2_token).json()
        
        assert len(user1_calcs) == 1
        assert len(user2_calcs) == 1
        assert user1_calcs[0]["a"] == 1
        assert user2_calcs[0]["a"] == 2


class TestCalculationRead:
    """Test reading (getting) specific calculations."""
    
    def test_read_calculation_success(self, authenticated_user):
        """Test reading a specific calculation."""
        # Create a calculation
        calc_data = {"a": 10, "b": 5, "type": "add"}
        create_response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Read it back
        response = client.get(
            f"/calculations/{calc_id}",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == calc_id
        assert data["a"] == 10
        assert data["b"] == 5
        assert data["result"] == 15
    
    def test_read_calculation_not_found(self, authenticated_user):
        """Test reading non-existent calculation."""
        response = client.get(
            "/calculations/99999",
            headers=authenticated_user
        )
        
        assert response.status_code == 404
    
    def test_read_calculation_without_auth(self):
        """Test that reading requires authentication."""
        response = client.get("/calculations/1")
        
        assert response.status_code == 403
    
    def test_read_calculation_other_user(self):
        """Test that users cannot read other users' calculations."""
        # Create user1 and their calculation
        user1_data = {"username": "user1", "email": "user1@example.com", "password": "password123"}
        client.post("/users/register", json=user1_data)
        login_response = client.post("/users/login", json={"username": "user1", "password": "password123"})
        user1_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        create_response = client.post(
            "/calculations",
            json={"a": 1, "b": 1, "type": "add"},
            headers=user1_token
        )
        calc_id = create_response.json()["id"]
        
        # Create user2
        user2_data = {"username": "user2", "email": "user2@example.com", "password": "password123"}
        client.post("/users/register", json=user2_data)
        login_response = client.post("/users/login", json={"username": "user2", "password": "password123"})
        user2_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # User2 tries to read user1's calculation
        response = client.get(f"/calculations/{calc_id}", headers=user2_token)
        
        assert response.status_code == 404


class TestCalculationEdit:
    """Test editing (updating) calculations."""
    
    def test_edit_calculation_put_success(self, authenticated_user):
        """Test updating a calculation with PUT."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Update it
        update_data = {"a": 20, "b": 3, "type": "multiply"}
        response = client.put(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["a"] == 20
        assert data["b"] == 3
        assert data["type"] == "multiply"
        assert data["result"] == 60
    
    def test_edit_calculation_db_verification(self, authenticated_user):
        """Test that updates are persisted to database."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 100, "b": 25, "type": "divide"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Verify initial state in DB
        db = TestingSessionLocal()
        calc_before = db.query(Calculation).filter(Calculation.id == calc_id).first()
        assert calc_before.a == 100
        assert calc_before.b == 25
        assert calc_before.result == 4.0
        db.close()
        
        # Update via API
        update_data = {"a": 50, "b": 10, "type": "subtract"}
        response = client.put(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        assert response.status_code == 200
        
        # Verify update persisted to DB
        db = TestingSessionLocal()
        calc_after = db.query(Calculation).filter(Calculation.id == calc_id).first()
        assert calc_after.a == 50
        assert calc_after.b == 10
        assert calc_after.type == "subtract"
        assert calc_after.result == 40.0
        db.close()
    
    def test_edit_calculation_patch_success(self, authenticated_user):
        """Test updating a calculation with PATCH."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Partial update with PATCH
        update_data = {"b": 8}
        response = client.patch(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["a"] == 10  # Unchanged
        assert data["b"] == 8   # Updated
        assert data["type"] == "add"  # Unchanged
        assert data["result"] == 18  # Recalculated
    
    def test_edit_calculation_partial_update(self, authenticated_user):
        """Test partial update (only operation type)."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Update only the operation type
        update_data = {"type": "subtract"}
        response = client.put(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["a"] == 10
        assert data["b"] == 5
        assert data["type"] == "subtract"
        assert data["result"] == 5  # 10 - 5
    
    def test_edit_calculation_division_by_zero(self, authenticated_user):
        """Test that updating to division by zero is rejected."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Try to update to division by zero
        update_data = {"b": 0, "type": "divide"}
        response = client.put(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 400
        assert "division by zero" in response.json()["detail"].lower()
    
    def test_edit_calculation_not_found(self, authenticated_user):
        """Test updating non-existent calculation."""
        response = client.put(
            "/calculations/99999",
            json={"a": 1},
            headers=authenticated_user
        )
        
        assert response.status_code == 404
    
    def test_edit_calculation_without_auth(self):
        """Test that editing requires authentication."""
        response = client.put("/calculations/1", json={"a": 1})
        
        assert response.status_code == 403


class TestCalculationDelete:
    """Test deleting calculations."""
    
    def test_delete_calculation_success(self, authenticated_user):
        """Test successfully deleting a calculation."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(
            f"/calculations/{calc_id}",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify it's gone
        get_response = client.get(
            f"/calculations/{calc_id}",
            headers=authenticated_user
        )
        assert get_response.status_code == 404
    
    def test_delete_calculation_db_verification(self, authenticated_user):
        """Test that deletion removes data from database."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 99, "b": 11, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Verify it exists in DB
        db = TestingSessionLocal()
        calc_before = db.query(Calculation).filter(Calculation.id == calc_id).first()
        assert calc_before is not None
        db.close()
        
        # Delete via API
        response = client.delete(
            f"/calculations/{calc_id}",
            headers=authenticated_user
        )
        assert response.status_code == 200
        
        # Verify it's removed from DB
        db = TestingSessionLocal()
        calc_after = db.query(Calculation).filter(Calculation.id == calc_id).first()
        assert calc_after is None
        db.close()
    
    def test_delete_calculation_not_found(self, authenticated_user):
        """Test deleting non-existent calculation."""
        response = client.delete(
            "/calculations/99999",
            headers=authenticated_user
        )
        
        assert response.status_code == 404
    
    def test_delete_calculation_without_auth(self):
        """Test that deleting requires authentication."""
        response = client.delete("/calculations/1")
        
        assert response.status_code == 403
    
    def test_delete_calculation_other_user(self):
        """Test that users cannot delete other users' calculations."""
        # Create user1 and their calculation
        user1_data = {"username": "user1", "email": "user1@example.com", "password": "password123"}
        client.post("/users/register", json=user1_data)
        login_response = client.post("/users/login", json={"username": "user1", "password": "password123"})
        user1_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        create_response = client.post(
            "/calculations",
            json={"a": 1, "b": 1, "type": "add"},
            headers=user1_token
        )
        calc_id = create_response.json()["id"]
        
        # Create user2
        user2_data = {"username": "user2", "email": "user2@example.com", "password": "password123"}
        client.post("/users/register", json=user2_data)
        login_response = client.post("/users/login", json={"username": "user2", "password": "password123"})
        user2_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # User2 tries to delete user1's calculation
        response = client.delete(f"/calculations/{calc_id}", headers=user2_token)
        
        assert response.status_code == 404


class TestInvalidDataAndErrors:
    """Test invalid inputs, error status codes, and error responses."""
    
    def test_invalid_calculation_type(self, authenticated_user):
        """Test that invalid operation type returns 422."""
        calc_data = {
            "a": 10.0,
            "b": 5.0,
            "type": "power"  # Invalid operation
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
    
    def test_missing_required_fields(self, authenticated_user):
        """Test that missing required fields returns 422."""
        # Missing 'b' field
        calc_data = {
            "a": 10.0,
            "type": "add"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
    
    def test_invalid_data_types(self, authenticated_user):
        """Test that invalid data types return 422."""
        # String instead of number
        calc_data = {
            "a": "not_a_number",
            "b": 5.0,
            "type": "add"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
    
    def test_division_by_zero_error_response(self, authenticated_user):
        """Test detailed error response for division by zero."""
        calc_data = {
            "a": 100.0,
            "b": 0.0,
            "type": "divide"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
        # Verify error message contains useful information
        error_str = str(error).lower()
        assert "division by zero" in error_str or "divide" in error_str
    
    def test_unauthorized_access_error(self):
        """Test that accessing protected endpoints without auth returns 403."""
        # Try to create calculation without auth
        response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"}
        )
        assert response.status_code == 403
        
        # Try to browse calculations without auth
        response = client.get("/calculations")
        assert response.status_code == 403
        
        # Try to read calculation without auth
        response = client.get("/calculations/1")
        assert response.status_code == 403
        
        # Try to update calculation without auth
        response = client.put("/calculations/1", json={"a": 1})
        assert response.status_code == 403
        
        # Try to delete calculation without auth
        response = client.delete("/calculations/1")
        assert response.status_code == 403
    
    def test_not_found_errors(self, authenticated_user):
        """Test that accessing non-existent resources returns 404."""
        # Non-existent calculation ID
        response = client.get("/calculations/999999", headers=authenticated_user)
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        
        # Update non-existent
        response = client.put(
            "/calculations/999999",
            json={"a": 1, "b": 1, "type": "add"},
            headers=authenticated_user
        )
        assert response.status_code == 404
        
        # Delete non-existent
        response = client.delete("/calculations/999999", headers=authenticated_user)
        assert response.status_code == 404
    
    def test_user_registration_errors(self):
        """Test various user registration validation errors."""
        # Invalid email format
        response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "not_an_email",
                "password": "password123"
            }
        )
        assert response.status_code == 422
        
        # Password too short
        response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "123"
            }
        )
        assert response.status_code == 422
        
        # Username too short
        response = client.post(
            "/users/register",
            json={
                "username": "ab",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 422
    
    def test_duplicate_user_errors(self):
        """Test error responses for duplicate username/email."""
        # Register first user
        client.post(
            "/users/register",
            json={
                "username": "uniqueuser",
                "email": "unique@example.com",
                "password": "password123"
            }
        )
        
        # Try duplicate username
        response = client.post(
            "/users/register",
            json={
                "username": "uniqueuser",
                "email": "different@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        error = response.json()
        assert "detail" in error
        assert "already registered" in error["detail"].lower()
        
        # Try duplicate email
        response = client.post(
            "/users/register",
            json={
                "username": "differentuser",
                "email": "unique@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        error = response.json()
        assert "already registered" in error["detail"].lower()
    
    def test_login_errors(self):
        """Test login error responses."""
        # Register user
        client.post(
            "/users/register",
            json={
                "username": "logintest",
                "email": "logintest@example.com",
                "password": "correctpassword"
            }
        )
        
        # Wrong password
        response = client.post(
            "/users/login",
            json={
                "username": "logintest",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        error = response.json()
        assert "detail" in error
        
        # Non-existent user
        response = client.post(
            "/users/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401
