from django.db import models
from django.contrib.auth import get_user_model
from books.models import Book
from django.db.models import Q

User = get_user_model()


class Thread(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    participants = models.ManyToManyField(User, related_name="threads")
    participants_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thread {self.id} - Participants: {', '.join(user.username for user in self.participants.all())}"


class Message(models.Model):
    thread = models.ForeignKey(Thread, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(~Q(content="")) & Q(content__isnull=False) & Q(book__isnull=True)) |
                    (Q(content__isnull=True) | Q(content="")) & Q(book__isnull=False)
                ),
                name="message_either_content_or_book"
            )
        ]

    def __str__(self):
        return f"Message from {self.sender.username} in Thread {self.thread.id}"

