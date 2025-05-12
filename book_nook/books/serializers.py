from rest_framework import serializers
from django.db.models import Avg
from .models import BookReview, Book
from .utils import get_or_create_book


class GoogleBookSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField(source="volumeInfo.title", default="No Title")
    authors = serializers.ListField(source="volumeInfo.authors", default=["Unknown"])
    description = serializers.CharField(source="volumeInfo.description", required=False, allow_blank=True)
    thumbnail = serializers.CharField(source="volumeInfo.imageLinks.thumbnail", default="")

    rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    def get_reviews_count(self, obj):
        book_id = obj.get("id")
        return BookReview.objects.filter(book__id=book_id).count()
    
    def get_rating(self, obj):
        book_id = obj.get("id")
        reviews = BookReview.objects.filter(book__id=book_id)
        if reviews:
            avg = reviews.aggregate(Avg('rating'))['rating__avg']
            return round(avg, 1)
        return None
    
    def get_is_saved(self, obj):
        request = self.context.get("request")
        book_id = obj.get("id")

        if request and request.user.is_authenticated:
            return Book.objects.filter(id=book_id, saved_by=request.user).exists()
        return False
    
        

class BookModelSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    class Meta:
        model = Book
        fields = ["id", "title", "authors", "description", "thumbnail", "rating", "reviews_count", "is_saved"]
        read_only_fields = fields

    def get_reviews_count(self, obj):
        book_id = obj.id
        return BookReview.objects.filter(book__id=book_id).count()
    
    def get_rating(self, obj):
        book_id = obj.id
        reviews = BookReview.objects.filter(book__id=book_id)
        if reviews:
            avg = reviews.aggregate(Avg('rating'))['rating__avg']
            return round(avg, 1)
        return None
    
    def get_is_saved(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(id=request.user.id).exists()
        return False


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    is_owner = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    class Meta:
        model = BookReview
        fields = ['review', 'user', 'created_at', 'id', 'is_owner', 'rating']
        read_only_fields = fields
    
    def get_is_owner(self, obj):
        request = self.context.get("request")
        return request.user == obj.user if request and request.user.is_authenticated else False
    
    def get_rating(self, obj):
        return obj.rating / 2
    

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookReview
        fields = ['review', 'rating']
    


class ToggleSaveBookSerializer(serializers.Serializer):
    book_data = serializers.DictField()

    def validate_book_data(self, value):
        if not value.get("book_id"):
            raise serializers.ValidationError("book_id is required.")
        return value

    def save(self, **kwargs):
        request = self.context.get("request")
        user = request.user
        book_data = self.validated_data["book_data"]

        book = get_or_create_book(book_data)

        if book in user.saved_books.all():
            user.saved_books.remove(book)
            is_saved = False
        else:
            user.saved_books.add(book)
            is_saved = True

        return {"book_id": book.id, "is_saved": is_saved}