from urllib import response

import requests
from django.conf import settings

HARDCOVER_URL = "https://api.hardcover.app/v1/graphql"


def search_books(query, page=1, per_page=20):
    print(f"Searching for books with query: {query}, page: {page}, per_page: {per_page}")

    graphql = """
    query SearchBooks(
        $query: String!,
        $page: Int!,
        $perPage: Int!
    ) {
        search(
            query: $query,
            query_type: "Book",
            page: $page,
            per_page: $perPage
        ) {
            results
            ids
        }
    }
    """

    payload = {
        "query": graphql,
        "variables": {
            "query": query,
            "page": page,
            "perPage": per_page,
        },
    }

    import json
    print(json.dumps(payload, indent=2))

    response = requests.post(
        HARDCOVER_URL,
        headers={
            "Authorization": f"Bearer {settings.HARDCOVER_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "query": graphql,
            "variables": {
                "query": query,
                "page": page,
                "perPage": per_page
            },
        }
    )

    response.raise_for_status()

    print(f"Received response: {response.json()}")

    books = response.json()["data"]["search"]["results"]["hits"]

    results = [
        b for b in books
        if (
            b["document"].get("ratings_count", 0) > 0
            and b["document"].get("description")
        )
    ]

    return results