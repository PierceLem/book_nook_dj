import requests
from django.http import JsonResponse
from django.conf import settings
from .serializers import BookSerializer


GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

def search_books(request):
    query = request.GET.get("q", "")
    max_results = request.GET.get("maxResults", 21)

    if not query:
        return JsonResponse({"error": "No search query provided"}, status=400)

    params = {
        "q": query,
        "maxResults": max_results,
        "key": settings.GOOGLE_BOOKS_API_KEY,
    }

    response = requests.get(GOOGLE_BOOKS_API_URL, params=params)

    if response.status_code == 200:
        books = response.json().get("items", [])

        serialized_books = BookSerializer(books, many=True).data

        return JsonResponse(serialized_books, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch data from Google Books API"}, status=response.status_code)
