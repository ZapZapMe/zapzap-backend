from fastapi.testclient import TestClient


def test_create_invoice(client: TestClient):
    # e.g. call POST /tips/ to create a new tip (which triggers invoice creation).
    payload = {
        "amount_sats": 123,
        "tweet_url": "https://x.com/imaginator/status/1878037256021188715",
        "tip_sender": "anonymous",
    }
    response = client.post("/tips/", json=payload)
    assert response.status_code == 200, f"Response text: {response.text}"
    data = response.json()
    assert "bolt11_invoice" in data, "Expected BOLT11 invoice to be returned"
    assert data["amount_sats"] == 123


# class TipInvoice(BaseModel):
#     tip_recipient: str
#     amount_sats: int
#     comment: Optional[str] = None
