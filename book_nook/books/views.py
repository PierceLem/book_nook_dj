import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions, status
from django.conf import settings
from .serializers import BookSerializer, ReviewSerializer, BookLikeSerializer
from .models import BookReview, BookLike
from .utils import get_or_create_book 


GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

class SearchBooks(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get("q", "")
        max_results = request.GET.get("maxResults", 20)

        if not query:
            return Response({"error": "No search query provided"}, status=400)

        params = {
            "q": query,
            "maxResults": max_results,
            "key": settings.GOOGLE_BOOKS_API_KEY,
        }

        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)

        if response.status_code == 200:
            books = response.json().get("items", [])
            serializer = BookSerializer(books, many=True, context={'request': request})

            return Response(serializer.data)
        else:
            return Response({"error": "Failed to fetch data from Google Books API"}, status=response.status_code)
    

class BookReviewList(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        book_id = self.kwargs["book_id"]
        return BookReview.objects.filter(book__book_id=book_id)


class CreateReview(generics.CreateAPIView):
    queryset = BookReview.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        book_id = self.request.data.get("book_id")
        book = get_or_create_book(book_id)
        serializer.save(user=self.request.user, book=book)


class ToggleBookLike(generics.GenericAPIView):
    serializer_class = BookLikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, book_id):
        book = get_or_create_book(book_id)
        user = request.user

        existing_like = BookLike.objects.filter(book=book, user=user).first()

        if existing_like:
            existing_like.delete()
            liked = False
        else:
            BookLike.objects.create(book=book, user=user)
            liked = True

        likes_count = BookLike.objects.filter(book=book).count()

        return Response({"book_id": book_id, "liked": liked, "likes_count": likes_count}, status=status.HTTP_200_OK)