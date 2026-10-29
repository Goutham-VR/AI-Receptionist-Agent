from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_current_admin

client = TestClient(app)

def test_pending_approvals_requires_authentication():
    response = client.get("/approvals/pending")
    assert response.status_code == 401
def test_approve_booking_requires_authentication():
    response = client.post("/approvals/999999/approve")
    assert response.status_code == 401
def test_reject_booking_requires_authentication():
    response = client.post("/approvals/999999/reject")
    assert response.status_code == 401