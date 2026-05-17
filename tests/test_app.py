import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

INITIAL_ACTIVITIES = copy.deepcopy(activities)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activity_state():
    """Reset the in-memory activities state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))


def test_root_redirects_to_index():
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities():
    # Arrange
    url = "/activities"
    expected_activity_keys = set(INITIAL_ACTIVITIES.keys())

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == expected_activity_keys
    assert payload["Chess Club"]["max_participants"] == 12


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "test.student@mergington.edu"
    url = f"/activities/{activity_name}/signup"
    assert email not in activities[activity_name]["participants"]

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    url = f"/activities/{activity_name}/signup"
    assert email in activities[activity_name]["participants"]

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "new.student@mergington.edu"
    url = f"/activities/{activity_name}/signup"

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    url = f"/activities/{activity_name}/participants/{email}"
    assert email in activities[activity_name]["participants"]

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_unknown_participant_returns_not_found():
    # Arrange
    activity_name = "Chess Club"
    email = "unknown.student@mergington.edu"
    url = f"/activities/{activity_name}/participants/{email}"
    assert email not in activities[activity_name]["participants"]

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"


def test_remove_participant_from_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "test.student@mergington.edu"
    url = f"/activities/{activity_name}/participants/{email}"

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
