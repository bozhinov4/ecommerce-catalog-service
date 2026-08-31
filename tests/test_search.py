from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.test_crud import create_category, product_payload


@pytest.fixture
def catalog(client: TestClient) -> dict[str, dict[str, Any]]:
    sports = create_category(client, name="Sports")
    footwear = create_category(client, name="Footwear", parent_id=sports["id"])
    apparel = create_category(client, name="Apparel", parent_id=sports["id"])
    basketball = create_category(client, name="Basketball")

    products = [
        product_payload(
            footwear["id"],
            title="Control Football Boots",
            sku="BOOT-CONTROL",
            price="99.99",
        ),
        product_payload(
            footwear["id"],
            title="Pro Speed Boots",
            sku="PRO-SPEED",
            price="149.99",
        ),
        product_payload(
            apparel["id"],
            title="Match Jersey",
            sku="JERSEY-001",
            price="49.99",
        ),
        product_payload(
            basketball["id"],
            title="Indoor Basketball",
            sku="BALL-BASKET",
            price="29.99",
        ),
        product_payload(
            sports["id"],
            title="100% Match Ball",
            sku="BALL-MATCH",
            price="25.00",
        ),
    ]
    for payload in products:
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 201

    return {
        "sports": sports,
        "footwear": footwear,
        "apparel": apparel,
        "basketball": basketball,
    }


def search(client: TestClient, query: str = "") -> dict[str, Any]:
    response = client.get(f"/api/v1/products/search{query}")
    assert response.status_code == 200
    return response.json()


def test_search_matches_title_or_sku_case_insensitively(
    client: TestClient,
    catalog: dict[str, dict[str, Any]],
) -> None:
    del catalog

    title_result = search(client, "?q=BOOTS")
    sku_result = search(client, "?q=pro-speed")

    assert [item["title"] for item in title_result["items"]] == [
        "Control Football Boots",
        "Pro Speed Boots",
    ]
    assert [item["sku"] for item in sku_result["items"]] == ["PRO-SPEED"]


def test_search_combines_exact_sku_and_inclusive_price_bounds(
    client: TestClient,
    catalog: dict[str, dict[str, Any]],
) -> None:
    del catalog

    price_result = search(client, "?min_price=49.99&max_price=99.99")
    sku_result = search(client, "?sku=boot-control&min_price=99.99&max_price=99.99")

    assert [item["title"] for item in price_result["items"]] == [
        "Control Football Boots",
        "Match Jersey",
    ]
    assert [item["sku"] for item in sku_result["items"]] == ["BOOT-CONTROL"]


def test_search_category_can_include_or_exclude_descendants(
    client: TestClient,
    catalog: dict[str, dict[str, Any]],
) -> None:
    sports_id = catalog["sports"]["id"]

    recursive = search(client, f"?category_id={sports_id}")
    direct = search(
        client,
        f"?category_id={sports_id}&include_descendants=false",
    )

    assert recursive["total"] == 4
    assert [item["title"] for item in direct["items"]] == ["100% Match Ball"]


def test_search_sorts_and_paginates_with_metadata(
    client: TestClient,
    catalog: dict[str, dict[str, Any]],
) -> None:
    del catalog

    result = search(client, "?sort=price_desc&page=2&page_size=2")

    assert result["total"] == 5
    assert result["pages"] == 3
    assert result["page"] == 2
    assert [item["title"] for item in result["items"]] == [
        "Match Jersey",
        "Indoor Basketball",
    ]


def test_search_escapes_like_wildcards(
    client: TestClient,
    catalog: dict[str, dict[str, Any]],
) -> None:
    del catalog

    result = search(client, "?q=%25")

    assert [item["title"] for item in result["items"]] == ["100% Match Ball"]


@pytest.mark.parametrize(
    "query",
    [
        "?min_price=100&max_price=50",
        "?page=0",
        "?page_size=101",
        "?unexpected=true",
    ],
)
def test_search_rejects_invalid_queries(client: TestClient, query: str) -> None:
    assert client.get(f"/api/v1/products/search{query}").status_code == 422
