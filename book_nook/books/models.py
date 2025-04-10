from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Book(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=500)
    authors = models.JSONField(default=list)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.URLField(blank=True, null=True)
    saved_by = models.ManyToManyField(User, related_name='saved_books', blank=True)

    def __str__(self):
        return self.title
    
    def get_likes_count(self):
        return self.likes.count()


class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews", null=True, to_field="id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    review = models.TextField(max_length=1000)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        default=5
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['book']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Review by {self.user} on {self.book}"

