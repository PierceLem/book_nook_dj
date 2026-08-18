from rest_framework import serializers
from django.db.models import Avg
from .models import BookReview, Book
from .utils import get_or_create_book
from accounts.serializers import NookUserSerializer



class HardcoverBookSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.get("id")

    def get_title(self, obj):
        return obj.get("title")

    def get_authors(self, obj):
        return obj.get("author_names", [])

    def get_description(self, obj):
        return obj.get("description")

    def get_thumbnail(self, obj):
        image = obj.get("image")
        if image:
            return image.get("url")
        return None

    def get_is_saved(self, obj):
        saved_book_ids = self.context.get("saved_book_ids", set())
        return obj.get("id") in saved_book_ids

    def get_average_rating(self, obj):
        stats = self.context.get("review_stats", {}).get(obj.get("id"))
        if stats and stats["average_rating"] is not None:
            return round(stats["average_rating"] / 2, 1)
        return None

    def get_review_count(self, obj):
        stats = self.context.get("review_stats", {}).get(obj.get("id"))
        return stats["review_count"] if stats else 0
        

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
            rounded_avg = round(avg)
            return rounded_avg / 2
        return None
    
    def get_is_saved(self, obj):
        pass
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(id=request.user.id).exists()
        return False


class ReviewSerializer(serializers.ModelSerializer):
    user = NookUserSerializer()
    rating = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    class Meta:
        model = BookReview
        fields = ['review', 'user', 'created_at', 'id', 'rating', 'is_owner']
        read_only_fields = fields
    
    def get_rating(self, obj):
        return obj.rating / 2
    
    def get_is_owner(self, obj):
        request = self.context.get("request")
        return obj.user.id == request.user.id
    

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookReview
        fields = ['review', 'rating']
    


class ToggleSaveBookSerializer(serializers.Serializer):
    book_data = serializers.DictField()

    def validate_book_data(self, value):
        if not value.get("id"):
            raise serializers.ValidationError("id is required.")
        if not value.get("title"):
            raise serializers.ValidationError("title is required.")
        return value

    def save(self, **kwargs):
        request = self.context.get("request")
        user = request.user
        book_data = self.validated_data["book_data"]

        book = get_or_create_book(book_data)
        if book is None:
            raise serializers.ValidationError("Could not create or retrieve the book.")

        if user.saved_books.filter(pk=book.pk).exists():
            user.saved_books.remove(book)
            is_saved = False
        else:
            user.saved_books.add(book)
            is_saved = True

        return {"book_id": book.id, "is_saved": is_saved}