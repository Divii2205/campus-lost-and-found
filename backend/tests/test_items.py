# the health route should say the app is up
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


# the ready route should check that the database works
def test_ready_checks_database(client):
    assert client.get("/ready").json() == {"status": "READY"}


# a new item should be saved and sent back with an id
def test_create_item(client, sample_item):
    response = client.post("/api/items", json=sample_item)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == sample_item["title"]
    assert body["status"] == "FOUND"
    assert body["claimed_by"] is None


# bad data should be refused with a 422 error
def test_create_item_rejects_bad_input(client, sample_item):
    assert client.post("/api/items", json={**sample_item, "title": ""}).status_code == 422
    assert client.post("/api/items", json={**sample_item, "category": "PETS"}).status_code == 422
    # a new report can only be lost or found and never claimed
    assert client.post("/api/items", json={**sample_item, "status": "CLAIMED"}).status_code == 422


# listing should work with the status filter and the search word
def test_list_and_filter_items(client, sample_item):
    client.post("/api/items", json=sample_item)
    client.post("/api/items", json={**sample_item, "title": "Blue water bottle", "category": "BOTTLE",
                                    "status": "LOST", "location": "Sports complex"})
    assert len(client.get("/api/items").json()) == 2
    lost = client.get("/api/items", params={"status": "lost"}).json()
    assert [item["title"] for item in lost] == ["Blue water bottle"]
    search = client.get("/api/items", params={"q": "library"}).json()
    assert [item["title"] for item in search] == ["Black HP laptop charger"]


# getting one item should work and a missing item should give 404
def test_get_item_and_404(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    assert client.get(f"/api/items/{created['id']}").json()["location"] == sample_item["location"]
    assert client.get("/api/items/9999").status_code == 404


# updating should change only the fields that were sent
def test_update_item(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    response = client.put(f"/api/items/{created['id']}", json={"location": "Security office", "description": "Handed to guard"})
    assert response.status_code == 200
    assert response.json()["location"] == "Security office"
    assert response.json()["title"] == sample_item["title"]


# an item can be claimed once and a second claim gives 409
def test_claim_item_only_once(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    response = client.patch(f"/api/items/{created['id']}/claim", json={"claimed_by": "Rahul"})
    assert response.status_code == 200
    assert response.json()["status"] == "CLAIMED"
    assert response.json()["claimed_by"] == "Rahul"
    assert client.patch(f"/api/items/{created['id']}/claim", json={"claimed_by": "Someone"}).status_code == 409


# a deleted item should be gone and deleting it again gives 404
def test_delete_item(client, sample_item):
    created = client.post("/api/items", json=sample_item).json()
    assert client.delete(f"/api/items/{created['id']}").status_code == 204
    assert client.get(f"/api/items/{created['id']}").status_code == 404
    assert client.delete(f"/api/items/{created['id']}").status_code == 404


# stats should count lost and found and claimed items
def test_stats(client, sample_item):
    first = client.post("/api/items", json=sample_item).json()
    client.post("/api/items", json={**sample_item, "status": "LOST"})
    client.post("/api/items", json={**sample_item, "status": "LOST"})
    client.patch(f"/api/items/{first['id']}/claim", json={"claimed_by": "Owner"})
    assert client.get("/api/items/stats").json() == {"total": 3, "lost": 2, "found": 0, "claimed": 1}


# the metrics route should show prometheus numbers
def test_metrics_endpoint(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
