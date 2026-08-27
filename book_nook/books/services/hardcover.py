import requests
from django.conf import settings

HARDCOVER_URL = "https://api.hardcover.app/v1/graphql"


def search_books(query, page=1, per_page=20):
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

    hits = response.json()["data"]["search"]["results"]["hits"]

    books = [
        hit["document"] for hit in hits
        if (
            hit["document"].get("ratings_count", 0) > 0
            and hit["document"].get("description")
        )
    ]
    total = response.json()["data"]["search"]["results"]["found"]

    return books, total


def filter_books(tags, limit=20, offset=0):
    graphql = """
    query FilterBooks(
        $tags: [String!],
        $limit: Int!,
        $offset: Int!
    ) {
        books(
            where: {
                taggings: {
                    tag: {
                        tag: {
                            _in: $tags
                        }
                    }
                },
                ratings_count: {
                    _gt: 10
                },
                description: {
                    _is_null: false
                }
            },
            limit: $limit,
            offset: $offset
        ) {
            id
            title
            description
            ratings_count
            image {
                url
            }
        }
        books_aggregate {
            aggregate {
            count
            }
        }
    }
    """

    response = requests.post(
        HARDCOVER_URL,
        headers={
            "Authorization": f"Bearer {settings.HARDCOVER_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "query": graphql,
            "variables": {
                "tags": tags,
                "limit": limit,
                "offset": offset,
            },
        },
    )

    response.raise_for_status()

    books = response.json()["data"]["books"]
    total = response.json()["data"]["books_aggregate"]["aggregate"]["count"]

    return books, total


def get_books_by_ids(book_ids):
    graphql = """
    query GetBooksByIds($ids: [Int!]) {
        books(
            where: {
                id: {
                    _in: $ids
                }
            }
        ) {
            id
            title
            description
            ratings_count
            image {
                url
            }
            contributions {
                author {
                    name
                }
            }
        }
    }
    """

    response = requests.post(
        HARDCOVER_URL,
        headers={
            "Authorization": f"Bearer {settings.HARDCOVER_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "query": graphql,
            "variables": {
                "ids": [int(id) for id in book_ids],
            },
        },
    )

    response.raise_for_status()

    books = response.json()["data"]["books"]

    return books