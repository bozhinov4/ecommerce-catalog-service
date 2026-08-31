from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient


def create_category(
    client: TestClient,
    *,
    name: str = "Footwear",
    parent_id: str | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/categories",
        json={"name": name, "parent_id": parent_id},
    )
    assert response.status_code == 201
    return response.json()


def product_payload(category_id: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Control Football Boots",
        "description": "Firm-ground boots for controlled touches.",
        "image": "https://example.com/control-boots.jpg",
        "sku": "boot-001",
        "price": "99.99",
        "category_id": category_id,
    }
    payload.update(overrides)
    return payload


def test_category_crud_and_cycle_protection(client: TestClient) -> None:
    root = create_category(client)
    child = create_category(client, name="Football Boots", parent_id=root["id"])

    list_response = client.get("/api/v1/categories")
    assert list_response.status_code == 200
    assert [item["name"] for item in list_response.json()] == [
        "Football Boots",
        "Footwear",
    ]

    cycle_response = client.put(
        f"/api/v1/categories/{root['id']}",
        json={"name": "Footwear", "parent_id": child["id"]},
    )
    assert cycle_response.status_code == 409

    blocked_delete = client.delete(f"/api/v1/categories/{root['id']}")
    assert blocked_delete.status_code == 409

    assert client.delete(f"/api/v1/categories/{child['id']}").status_code == 204
    assert client.delete(f"/api/v1/categories/{root['id']}").status_code == 204
    assert client.get(f"/api/v1/categories/{root['id']}").status_code == 404


def test_category_replace_and_missing_parent(client: TestClient) -> None:
    category = create_category(client)

    response = client.put(
        f"/api/v1/categories/{category['id']}",
        json={"name": "Updated Footwear", "parent_id": None},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Footwear"
    assert (
        client.post(
            "/api/v1/categories",
            json={"name": "Missing parent", "parent_id": str(uuid4())},
        ).status_code
        == 404
    )


def test_product_crud_and_sku_conflict(client: TestClient) -> None:
    category = create_category(client)
    create_response = client.post(
        "/api/v1/products",
        json=product_payload(category["id"]),
    )

    assert create_response.status_code == 201
    product = create_response.json()
    assert product["sku"] == "BOOT-001"
    assert product["price"] == "99.99"

    duplicate_response = client.post(
        "/api/v1/products",
        json=product_payload(category["id"], title="Duplicate"),
    )
    assert duplicate_response.status_code == 409

    list_response = client.get("/api/v1/products?offset=0&limit=10")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [product["id"]]

    replacement = product_payload(
        category["id"],
        title="Elite Football Boots",
        sku="BOOT-002",
        price="129.50",
    )
    replace_response = client.put(
        f"/api/v1/products/{product['id']}",
        json=replacement,
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["title"] == "Elite Football Boots"

    assert client.delete(f"/api/v1/products/{product['id']}").status_code == 204
    assert client.get(f"/api/v1/products/{product['id']}").status_code == 404


def test_product_validation_and_missing_category(client: TestClient) -> None:
    invalid_response = client.post(
        "/api/v1/products",
        json=product_payload(str(uuid4()), image="not-a-url", price="0"),
    )
    assert invalid_response.status_code == 422

    missing_category_response = client.post(
        "/api/v1/products",
        json=product_payload(str(uuid4())),
    )
    assert missing_category_response.status_code == 404


def test_list_pagination_is_bounded(client: TestClient) -> None:
    assert client.get("/api/v1/categories?limit=101").status_code == 422
    assert client.get("/api/v1/products?offset=-1").status_code == 422
