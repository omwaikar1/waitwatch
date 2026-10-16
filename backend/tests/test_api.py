"""HTTP layer: status codes, response shapes, validation."""

import uuid

from app.seed import VENUES


def report_body(minutes=15, device_id=None):
    return {"device_id": str(device_id or uuid.uuid4()), "wait_minutes": minutes}


async def test_health(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_list_venues(client):
    response = await client.get("/venues")

    assert response.status_code == 200
    venues = response.json()
    assert len(venues) == len(VENUES)
    assert set(venues[0]) == {"id", "name", "lat", "lng", "avg_wait_minutes", "report_count"}


async def test_post_report_returns_201_without_device_id(client):
    response = await client.post("/venues/1/reports", json=report_body(15))

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "venue_id", "wait_minutes", "created_at"}  # no device_id
    assert (body["venue_id"], body["wait_minutes"]) == (1, 15)


async def test_posted_report_shows_up_in_list(client):
    await client.post("/venues/1/reports", json=report_body(15))
    await client.post("/venues/1/reports", json=report_body(25))

    c4 = (await client.get("/venues")).json()[0]

    assert (c4["avg_wait_minutes"], c4["report_count"]) == (20.0, 2)


async def test_wait_minutes_out_of_range_is_422(client):
    for bad in (-1, 121, 500):
        response = await client.post("/venues/1/reports", json=report_body(bad))
        assert response.status_code == 422, bad


async def test_boundary_values_accepted(client):
    assert (await client.post("/venues/1/reports", json=report_body(0))).status_code == 201
    assert (await client.post("/venues/2/reports", json=report_body(120))).status_code == 201


async def test_invalid_device_id_is_422(client):
    response = await client.post(
        "/venues/1/reports", json={"device_id": "nope", "wait_minutes": 10}
    )

    assert response.status_code == 422


async def test_unknown_venue_is_404(client):
    response = await client.post("/venues/999/reports", json=report_body())

    assert response.status_code == 404
    assert response.json() == {"detail": "Venue not found"}


async def test_repeat_report_is_429_with_retry_after(client):
    device = uuid.uuid4()
    await client.post("/venues/1/reports", json=report_body(device_id=device))

    response = await client.post("/venues/1/reports", json=report_body(device_id=device))

    assert response.status_code == 429
    assert 0 < int(response.headers["Retry-After"]) <= 600
