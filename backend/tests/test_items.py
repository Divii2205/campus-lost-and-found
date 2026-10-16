def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_checks_database(client):
    assert client.get("/ready").json() == {"status": "READY"}


def test_create_item(client, sample_item):
    response = client.post("/api/items", json=sample_item)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == sample_item["title"]
    assert body["status"] == "FOUND"
    assert body["claimed_by"] is None


def test_create_item_rejects_bad_input(client, sample_item):
    assert client.post("/api/items", json={**sample_item, "title": ""}).status_code == 422
    assert client.post("/api/items", json={**sample_item, "category": "PETS"}).status_code == 422
    # a new report can only be LOST or FOUND, never CLAIMED
    assert client.post("/api/items", json={**sample_item, "status": "CLAIMED"}).status_code == 422


def test_list_and_filter_items(client, sample_item):
    client.post("/api/items", json=sample_item)
    client.post("/api/items", json={**sample_item, "title": "Blue water bottle", "category": "BOTTLE",
                                    "status": "LOST", "location": "Sports complex"})
    assert len(client.get("/api/items").json()) == 2
    lost = client.get("/api/items", params={"status": "lost"}).json()
    assert [item["title"] for item in lost] == ["Blue water bottle"]
    search = client.get("/api/items", params={"q": "library"}).json()
    assert [item["title"] for item in search] == ["Black HP laptop charger"]


def test_get_item_and_404(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    assert client.get(f"/api/items/{created['id']}").json()["location"] == sample_item["location"]
    assert client.get("/api/items/9999").status_code == 404


def test_update_item(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    response = client.put(f"/api/items/{created['id']}", json={"location": "Security office", "description": "Handed to guard"})
    assert response.status_code == 200
    assert response.json()["location"] == "Security office"
    assert response.json()["title"] == sample_item["title"]


def test_claim_item_only_once(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    response = client.patch(f"/api/items/{created['id']}/claim", json={"claimed_by": "Rahul"})
    assert response.status_code == 200
    assert response.json()["status"] == "CLAIMED"
    assert response.json()["claimed_by"] == "Rahul"
    assert client.patch(f"/api/items/{created['id']}/claim", json={"claimed_by": "Someone"}).status_code == 409


def test_delete_item(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    assert client.delete(f"/api/items/{created['id']}").status_code == 204
    assert client.get(f"/api/items/{created['id']}").status_code == 404
    assert client.delete(f"/api/items/{created['id']}").status_code == 404


def test_stats(client, sample_item):
    first = client.post("/api/items", json=sample_item).json()
    client.post("/api/items", json={**sample_item, "status": "LOST"})
    client.post("/api/items", json={**sample_item, "status": "LOST"})
    client.patch(f"/api/items/{first['id']}/claim", json={"claimed_by": "Owner"})
    assert client.get("/api/items/stats").json() == {"total": 3, "lost": 2, "found": 0, "claimed": 1}


def test_metrics_endpoint(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
