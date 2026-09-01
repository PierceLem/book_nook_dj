from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Book(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=500)
    saved_by = models.ManyToManyField(
        User,
        related_name='saved_books',
        through='SavedBook',
        blank=True,
    )

    def __str__(self):
        return self.title


class SavedBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-saved_at']


class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews", null=True, to_field="id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews", null=True)
    review = models.TextField(max_length=1000)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)], 
        default=10
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['book']),
            models.Index(fields=['user']),
        ]

        constraints = [
            models.UniqueConstraint(fields=['book', 'user'], name='unique_book_review')
        ]

    def __str__(self):
        return f"Review by {self.user} on {self.book}"
    
    def get_rating(self):
        return self.rating / 2

