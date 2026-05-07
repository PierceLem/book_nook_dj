from django.db import models
from django.contrib.auth import get_user_model
from books.models import Book
from django.db.models import Q

User = get_user_model()


class Thread(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    participants = models.ManyToManyField(User, related_name="threads")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thread {self.id} - Participants: {', '.join(user.username for user in self.participants.all())}"
    
    def reconcile_name(self):
        count = self.participants.count()

        if count > 2 and self.name is None:
            self.name = "Group chat"
            self.save(update_fields=["name"])

        elif count == 2 and self.name is not None:
            self.name = None
            self.save(update_fields=["name"])

    class Meta:
        ordering = ['-created_at']
    


class Message(models.Model):
    thread = models.ForeignKey(Thread, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.CASCADE)
    thread_update = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(content__isnull=False, content__gt="") | (
                    Q(book__isnull=True) & (Q(thread_update__isnull=True) | Q(thread_update=""))
                ),
                name="message_content_unique_field",
            ),

            models.CheckConstraint(
                check=~Q(book__isnull=False) | (
                    (Q(content__isnull=True) | Q(content="")) & (Q(thread_update__isnull=True) | Q(thread_update=""))
                ),
                name="message_book_unique_field",
            ),

            models.CheckConstraint(
                check=~Q(thread_update__isnull=False, thread_update__gt="") | (
                    (Q(content__isnull=True) | Q(content="")) & Q(book__isnull=True)
                ),
                name="message_thread_update_unique_field",
            ),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} in Thread {self.thread.id}"

