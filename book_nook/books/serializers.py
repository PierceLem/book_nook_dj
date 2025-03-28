from rest_framework import serializers
from .models import BookReview, BookLike, ReviewLike


class BookSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField(source="volumeInfo.title", default="No Title")
    authors = serializers.ListField(source="volumeInfo.authors", default=["Unknown"])
    description = serializers.CharField(source="volumeInfo.description", required=False, allow_blank=True)
    published_date = serializers.CharField(source="volumeInfo.publishedDate", default="N/A")
    thumbnail = serializers.CharField(source="volumeInfo.imageLinks.thumbnail", default="")

    likes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()

    def get_likes(self, obj):
        book_id = obj.get("id")
        return BookLike.objects.filter(book__book_id=book_id).count()
    
    def get_liked(self, obj):
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            book_id = obj.get("id")
            return BookLike.objects.filter(book__book_id=book_id, user=request.user).exists()
        
        return False


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    likes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    class Meta:
        model = BookReview
        fields = ['review', 'user', 'book_id', 'created_at', 'likes', 'liked', 'id']
        read_only_fields = ['user', 'created_at', 'likes', 'id']

    def get_likes(self, obj):
        return ReviewLike.objects.filter(review=obj).count()
    
    def get_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ReviewLike.objects.filter(review=obj, user=request.user).exists()
        return False


class BookLikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    likes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    class Meta:
        model = BookLike
        fields = ['book', 'user', 'likes', 'liked']
        read_only_fields = ['user', 'likes']

    def get_likes(self, obj):
        return BookLike.objects.filter(book=obj.book).count()
    
    def get_liked(self, obj):
        request = self.context.get("request")
        return BookLike.objects.filter(book__book_id=obj.id, user=request.user).exists()
    

class ReviewLikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    likes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    class Meta:
        model = ReviewLike
        fields = ['review', 'user', 'likes', 'liked']
        read_only_fields = ['user', 'likes']

    def get_likes(self, obj):
        return ReviewLike.objects.filter(review=obj.review).count()
    
    def get_liked(self, obj):
        request = self.context.get("request")
        return ReviewLike.objects.filter(review__id=obj.id, user=request.user).exists()