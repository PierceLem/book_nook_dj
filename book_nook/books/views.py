import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions, status
from django.conf import settings
from .serializers import GoogleBookSerializer, ReviewSerializer, BookModelSerializer, ToggleSaveBookSerializer
from .models import BookReview, Book
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
            serializer = GoogleBookSerializer(books, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            return Response({"error": "Failed to fetch data from Google Books API"}, status=response.status_code)
        


class UserBookshelf(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        reviewed_books = Book.objects.filter(reviews__user=user).distinct()
        saved_books = Book.objects.filter(saved_by=user)

        data = {
            "reviewed_books": BookModelSerializer(reviewed_books, many=True, context={"request": request}).data,
            "saved_books": BookModelSerializer(saved_books, many=True, context={"request": request}).data,
        }
        return Response(data)
    
    

class BookReviewList(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        book_id = self.kwargs["book_id"]
        return BookReview.objects.filter(book__id=book_id)



class CreateReview(generics.CreateAPIView):
    queryset = BookReview.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        book_data = self.request.data.get("book_data") 
        book = get_or_create_book(book_data)
        serializer.save(user=self.request.user, book=book)



class ToggleSaveBook(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ToggleSaveBookSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result)
