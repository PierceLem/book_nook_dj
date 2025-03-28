from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Book(models.Model):
    book_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.book_id
    
    def get_likes_count(self):
        return self.likes.count()

class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews", null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    review = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} on {self.book.book_id}"
    
    def likes_count(self): 
        return self.likes.count()

class ReviewLike(models.Model):
    review = models.ForeignKey(BookReview, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class BookLike(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="likes", null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
