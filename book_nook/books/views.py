import requests
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions, status
from .serializers import HardcoverBookSerializer, ReviewSerializer, ReviewCreateSerializer, BookModelSerializer, ToggleSaveBookSerializer
from .models import BookReview, Book
from .utils import get_or_create_book 
from .services import hardcover


class SearchBooks(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        books = hardcover.search_books(request.GET.get("q"))

        serializer = HardcoverBookSerializer(
            books,
            many=True,
            context={"request": request}
        )

        return Response({
            "books": serializer.data,
        })
        


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
    
    

class BookReviewList(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        all_reviews = BookReview.objects.filter(book=book).order_by('created_at')

        if request.user.is_authenticated:
            user_review = all_reviews.filter(user=request.user).first()
            other_reviews = all_reviews.exclude(user=request.user)
            
            if user_review:
                combined_reviews = [user_review] + list(other_reviews)
            else:
                combined_reviews = list(all_reviews)
        else:
            combined_reviews = list(all_reviews)

        serialized = ReviewSerializer(combined_reviews, many=True, context={'request': request}).data
        return Response(serialized)



class ReviewOptions(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        review_id = request.data.get("id")
        book_data = request.data.get("book_data", {})
        book = get_or_create_book(book_data)

        if review_id:
            review = get_object_or_404(BookReview, id=review_id, user=user)
            serializer = ReviewCreateSerializer(review, data=request.data, partial=True)
        else:
            serializer = ReviewCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        review_instance = serializer.save(user=user, book=book)

        response_data = ReviewSerializer(review_instance, context={'request': request}).data
        return Response(response_data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        review_id = request.data.get("id")
        review = get_object_or_404(BookReview, id=review_id, user=request.user)
        review.delete()
        return Response({"detail": "Review deleted."}, status=status.HTTP_204_NO_CONTENT)



class ToggleSaveBook(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ToggleSaveBookSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result)
