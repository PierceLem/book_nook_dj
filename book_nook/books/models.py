from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class BookReview(models.Model):
    book_id = models.CharField(max_length=50, unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ReviewLike(models.Model):
    review = models.ForeignKey(BookReview, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class BookLike(models.Model):
    book_id = models.CharField(max_length=50, unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
