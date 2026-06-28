from fastapi.testclient import TestClient

from app.main import app
from app.services import auth_service


client = TestClient(app)


def test_root_route():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "TravelBuddiez backend is running"
    }


## Test /auth/register
def test_register_user_success(monkeypatch):
    from app.routes import auth_routes

    fake_user = auth_service.User(
        username="test",
        email="test@example.com",
        disabled=False,
    )

    def fake_create_user(username, email, password):
        return fake_user

    monkeypatch.setattr(
        auth_routes,
        "create_user",
        fake_create_user,
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "test",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "test"
    assert response.json()["email"] == "test@example.com"


def test_register_user_short_password():
    response = client.post(
        "/auth/register",
        json={
            "username": "test",
            "email": "test@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Password must be at least 8 characters long"


# Test /auth/token
def test_login_success(monkeypatch):
    from app.routes import auth_routes

    fake_user = auth_service.UserInDB(
        username="test",
        email="test@example.com",
        disabled=False,
        hashed_password="fakehash",
    )

    def fake_authenticate_user(username_or_email, password):
        return fake_user

    def fake_create_access_token(data, expires_delta):
        return "fake-jwt-token"

    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        fake_authenticate_user,
    )

    monkeypatch.setattr(
        auth_routes,
        "create_access_token",
        fake_create_access_token,
    )

    response = client.post(
        "/auth/token",
        data={
            "username": "test",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "fake-jwt-token",
        "token_type": "bearer",
    }


def test_login_wrong_password(monkeypatch):
    from app.routes import auth_routes

    def fake_authenticate_user(username_or_email, password):
        return False

    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        fake_authenticate_user,
    )

    response = client.post(
        "/auth/token",
        data={
            "username": "test",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


# Test /auth/me
def test_read_users_me_success():
    from app.routes.auth_routes import get_current_active_user

    fake_user = auth_service.User(
        username="test",
        email="test@example.com",
        disabled=False,
    )

    async def fake_get_current_active_user():
        return fake_user

    app.dependency_overrides[get_current_active_user] = fake_get_current_active_user

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer fake-token"
        },
    )

    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json()["username"] == "test"
    assert response.json()["email"] == "test@example.com"


#Test destination update routes
def test_seed_destinations_success(monkeypatch):
    from app.routes import destination_routes

    def fake_seed_destinations():
        return {
            "inserted": 3,
            "skipped": 0,
        }

    monkeypatch.setattr(
        destination_routes,
        "seed_destinations",
        fake_seed_destinations,
    )

    response = client.put("/destinations/seed")

    assert response.status_code == 200
    assert response.json()["message"] == "Destinations seeded successfully"
    assert response.json()["result"]["inserted"] == 3


def test_update_all_map_scores_success(monkeypatch):
    from app.routes import destination_routes

    def fake_update_map_scores():
        return 195

    monkeypatch.setattr(
        destination_routes,
        "update_map_scores",
        fake_update_map_scores,
    )

    response = client.put("/destinations/map-scores/update-all")

    assert response.status_code == 200
    assert response.json()["message"] == "195 map scores updated successfully"


def test_update_all_destinations_success(monkeypatch):
    from app.routes import destination_routes

    def fake_update_all_destinations():
        return {
            "updatedCount": 2,
            "results": [
                {"countryCode": "JPN"},
                {"countryCode": "SGP"},
            ],
        }

    monkeypatch.setattr(
        destination_routes,
        "update_all_destinations",
        fake_update_all_destinations,
    )

    response = client.put("/destinations/update-all")

    assert response.status_code == 200
    assert response.json()["message"] == "2 destinations updated successfully"
    assert len(response.json()["results"]) == 2


def test_update_one_destination_success(monkeypatch):
    from app.routes import destination_routes

    def fake_update_one_destination(country_code):
        return {
            "countryCode": country_code.upper(),
            "travelScore": 85,
            "riskLevel": "Low",
        }

    monkeypatch.setattr(
        destination_routes,
        "update_one_destination",
        fake_update_one_destination,
    )

    response = client.put("/destinations/JPN/update")

    assert response.status_code == 200
    assert response.json()["message"] == "JPN updated successfully"
    assert response.json()["updatedScore"]["travelScore"] == 85


def test_update_one_destination_not_found(monkeypatch):
    from app.routes import destination_routes

    def fake_update_one_destination(country_code):
        raise ValueError("Destination not found")

    monkeypatch.setattr(
        destination_routes,
        "update_one_destination",
        fake_update_one_destination,
    )

    response = client.put("/destinations/XXX/update")

    assert response.status_code == 404
    assert response.json()["detail"] == "Destination not found"


# Test GET /destinations without real DB
class FakeCursor:
    def __init__(self, fetchone_data=None, fetchall_data=None):
        self.fetchone_data = fetchone_data
        self.fetchall_data = fetchall_data
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        return self.fetchone_data

    def fetchall(self):
        return self.fetchall_data

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor

    def cursor(self):
        return self.fake_cursor

    def close(self):
        pass


def test_get_all_destinations_success(monkeypatch):
    from app.routes import destination_routes

    fake_destinations = [
        {
            "countryCode": "JPN",
            "country": "Japan",
            "city": "Tokyo",
            "mapScore": 90,
            "riskLevel": "Low",
            "condition": "Exercise normal precautions",
            "lastUpdated": "2026-06-29",
        }
    ]

    fake_cursor = FakeCursor(fetchall_data=fake_destinations)
    fake_connection = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_connection

    def fake_check_last_updated_map_scores(hours):
        return None

    monkeypatch.setattr(
        destination_routes,
        "get_connection",
        fake_get_connection,
    )

    monkeypatch.setattr(
        destination_routes,
        "check_last_updated_map_scores",
        fake_check_last_updated_map_scores,
    )

    response = client.get("/destinations")

    assert response.status_code == 200
    assert response.json()[0]["countryCode"] == "JPN"
    assert response.json()[0]["mapScore"] == 90


# Test GET /destinations/{country_code}
def test_get_destination_success(monkeypatch):
    from app.routes import destination_routes

    destination = {
        "id": 1,
        "countryCode": "JPN",
        "country": "Japan",
        "city": "Tokyo",
        "travelScore": 85,
        "riskLevel": "Low",
        "condition": "Safe to travel",
        "weather": "Clear sky",
        "news": "No major issues",
        "advisory": "Exercise normal precautions",
        "lastUpdated": "2026-06-29",
    }

    news_articles = [
        {
            "title": "Japan airport reopens",
            "abstractedSummary": "Airport operations have resumed.",
            "url": "https://example.com",
            "sourceName": "Example News",
            "publishedAt": "2026-06-29",
            "isRelevant": True,
        }
    ]

    class DestinationCursor(FakeCursor):
        def __init__(self):
            super().__init__()
            self.call_count = 0

        def fetchone(self):
            return destination

        def fetchall(self):
            return news_articles

    fake_cursor = DestinationCursor()
    fake_connection = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_connection

    monkeypatch.setattr(
        destination_routes,
        "get_connection",
        fake_get_connection,
    )

    response = client.get("/destinations/JPN")

    assert response.status_code == 200
    assert response.json()["countryCode"] == "JPN"
    assert response.json()["travelScore"] == 85
    assert len(response.json()["newsArticles"]) == 1
    assert response.json()["newsArticles"][0]["title"] == "Japan airport reopens"


def test_get_destination_not_found(monkeypatch):
    from app.routes import destination_routes

    fake_cursor = FakeCursor(fetchone_data=None)
    fake_connection = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_connection

    monkeypatch.setattr(
        destination_routes,
        "get_connection",
        fake_get_connection,
    )

    response = client.get("/destinations/XXX")

    assert response.status_code == 404
    assert response.json()["detail"] == "Destination not found"