from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()

class Thread(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    participants = models.ManyToManyField(User, related_name="threads")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thread {self.id} - Participants: {', '.join(user.username for user in self.participants.all())}"

class Message(models.Model):
    thread = models.ForeignKey(Thread, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in Thread {self.thread.id}"

