"""
Integration tests for user API endpoints.
These tests require a database connection.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models import User
import os

# Use SQLite for testing (no external database needed)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test.db"
)

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


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_user_success(self):
        """Test successful user registration."""
        response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
        assert "password_hash" not in data
        assert "id" in data
        assert "created_at" in data
    
    def test_register_user_db_verification(self):
        """Test that registration actually stores data in database."""
        # Register user
        response = client.post(
            "/users/register",
            json={
                "username": "dbuser",
                "email": "dbuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Verify data in database
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        
        assert user is not None
        assert user.username == "dbuser"
        assert user.email == "dbuser@example.com"
        assert user.is_active is True
        assert user.password_hash is not None
        assert user.password_hash != "password123"  # Should be hashed
        assert user.password_hash.startswith("$2b$")  # bcrypt format
        assert user.created_at is not None
        assert user.updated_at is not None
        
        db.close()
    
    def test_register_duplicate_username(self):
        """Test that duplicate username is rejected."""
        # Register first user
        client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "password123"
            }
        )
        
        # Try to register with same username
        response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_duplicate_email(self):
        """Test that duplicate email is rejected."""
        # Register first user
        client.post(
            "/users/register",
            json={
                "username": "testuser1",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/users/register",
            json={
                "username": "testuser2",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "not-an-email",
                "password": "password123"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self):
        """Test registration with password too short."""
        response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_short_username(self):
        """Test registration with username too short."""
        response = client.post(
            "/users/register",
            json={
                "username": "ab",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login endpoint."""
    
    def test_login_success(self):
        """Test successful login."""
        # Register user first
        client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # Login
        response = client.post(
            "/users/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "user" in data
        assert data["user"]["username"] == "testuser"
    
    def test_login_db_verification(self):
        """Test that login validates against database."""
        # Register user
        reg_response = client.post(
            "/users/register",
            json={
                "username": "loginuser",
                "email": "loginuser@example.com",
                "password": "securepass123"
            }
        )
        user_id = reg_response.json()["id"]
        
        # Verify user exists in DB
        db = TestingSessionLocal()
        user_before_login = db.query(User).filter(User.id == user_id).first()
        assert user_before_login is not None
        password_hash_before = user_before_login.password_hash
        db.close()
        
        # Login successfully
        login_response = client.post(
            "/users/login",
            json={
                "username": "loginuser",
                "password": "securepass123"
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        # Verify password hash hasn't changed (login doesn't modify it)
        db = TestingSessionLocal()
        user_after_login = db.query(User).filter(User.id == user_id).first()
        assert user_after_login.password_hash == password_hash_before
        db.close()
        
        # Try login with wrong password
        wrong_pass_response = client.post(
            "/users/login",
            json={
                "username": "loginuser",
                "password": "wrongpassword"
            }
        )
        assert wrong_pass_response.status_code == 401
    
    def test_login_with_email(self):
        """Test login using email instead of username."""
        # Register user first
        client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # Login with email
        response = client.post(
            "/users/login",
            json={
                "username": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
    
    def test_login_wrong_password(self):
        """Test login with incorrect password."""
        # Register user first
        client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # Login with wrong password
        response = client.post(
            "/users/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self):
        """Test login with user that doesn't exist."""
        response = client.post(
            "/users/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401


class TestUserCRUD:
    """Test user CRUD operations."""
    
    def test_get_all_users(self):
        """Test getting all users."""
        # Register multiple users
        for i in range(3):
            client.post(
                "/users/register",
                json={
                    "username": f"user{i}",
                    "email": f"user{i}@example.com",
                    "password": "password123"
                }
            )
        
        # Get all users
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_get_user_by_id(self):
        """Test getting a specific user by ID."""
        # Register user
        register_response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        user_id = register_response.json()["id"]
        
        # Get user by ID
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["id"] == user_id
    
    def test_get_nonexistent_user(self):
        """Test getting a user that doesn't exist."""
        response = client.get("/users/9999")
        assert response.status_code == 404
    
    def test_update_user(self):
        """Test updating user information."""
        # Register user
        register_response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        user_id = register_response.json()["id"]
        
        # Update user
        response = client.put(
            f"/users/{user_id}",
            json={
                "username": "updateduser",
                "email": "updated@example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updated@example.com"
    
    def test_update_user_duplicate_username(self):
        """Test updating user with username that already exists."""
        # Register two users
        client.post(
            "/users/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "password123"
            }
        )
        register_response = client.post(
            "/users/register",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "password123"
            }
        )
        user2_id = register_response.json()["id"]
        
        # Try to update user2 with user1's username
        response = client.put(
            f"/users/{user2_id}",
            json={"username": "user1"}
        )
        assert response.status_code == 400
    
    def test_delete_user(self):
        """Test deleting a user."""
        # Register user
        register_response = client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        user_id = register_response.json()["id"]
        
        # Delete user
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
        
        # Verify user is deleted
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_user(self):
        """Test deleting a user that doesn't exist."""
        response = client.delete("/users/9999")
        assert response.status_code == 404


class TestPasswordHashing:
    """Test that passwords are properly hashed."""
    
    def test_password_not_stored_plaintext(self):
        """Test that passwords are hashed, not stored in plain text."""
        # Register user
        client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # Check database directly
        db = TestingSessionLocal()
        user = db.query(User).filter(User.username == "testuser").first()
        
        # Password hash should not equal plain password
        assert user.password_hash != "password123"
        # Password hash should be bcrypt format
        assert user.password_hash.startswith("$2b$")
        
        db.close()
