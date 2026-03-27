"""
Tests for the Mergington High School Extracurricular Activities API

Tests all endpoints of the FastAPI application including:
- Root endpoint redirect
- Getting all activities
- Signing up for activities
- Removing signups from activities

Uses AAA (Arrange-Act-Assert) testing pattern for clarity.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state after each test"""
    from src.app import activities
    import copy
    
    initial_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(initial_activities)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that the root endpoint redirects to static/index.html"""
        # Arrange
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self):
        """Test retrieving all activities"""
        # Arrange
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Digital Art Studio", "Theater Club", "Debate Club", "Science Club"
        ]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) >= len(expected_activities)
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        for activity_name, activity_info in data.items():
            for field in required_fields:
                assert field in activity_info
            assert isinstance(activity_info["participants"], list)
    
    def test_activity_participants_are_emails(self):
        """Test that participants are email addresses"""
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        for activity_name, activity_info in data.items():
            for participant in activity_info["participants"]:
                assert "@" in participant


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, reset_activities):
        """Test successfully signing up for an activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify signup was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        email = "teststudent@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in final_response.json()[activity_name]["participants"]
    
    def test_signup_for_nonexistent_activity(self, reset_activities):
        """Test that signing up for a non-existent activity returns 404"""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Club"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_signed_up(self, reset_activities):
        """Test that a student already signed up gets a 400 error"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_missing_email(self, reset_activities):
        """Test that signup without email parameter fails"""
        # Act
        response = client.post("/activities/Chess Club/signup")
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity


class TestRemoveSignup:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_remove_signup_success(self, reset_activities):
        """Test successfully removing a student from an activity"""
        # Arrange
        email = "removeme@mergington.edu"
        activity_name = "Basketball Team"
        
        # First sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
    
    def test_remove_signup_removes_participant(self, reset_activities):
        """Test that removing signup actually removes the participant"""
        # Arrange
        email = "toremove@mergington.edu"
        activity_name = "Programming Class"
        
        # First sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in final_response.json()[activity_name]["participants"]
    
    def test_remove_from_nonexistent_activity(self, reset_activities):
        """Test that removing from a non-existent activity returns 404"""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Club"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_remove_not_signed_up_student(self, reset_activities):
        """Test that removing a student not signed up returns 400"""
        # Arrange
        email = "notsignedupstudent@mergington.edu"
        activity_name = "Tennis Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_remove_signup_missing_email(self, reset_activities):
        """Test that remove signup without email parameter fails"""
        # Act
        response = client.delete("/activities/Chess Club/signup")
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity