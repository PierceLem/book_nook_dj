from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            raise ValueError("The Username field must be set")

        email = self.normalize_email(email).lower()
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)


class NookUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username
    

class Friendship(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
    ]

    from_user = models.ForeignKey(NookUser, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(NookUser, related_name='friend_requests_received', on_delete=models.CASCADE)
    users_hash = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(from_user=models.F('to_user')),
                name='prevent_self_friendship'
            ),
            
            models.UniqueConstraint(
                fields=['from_user', 'to_user'],
                name='unique_friendship'
            ),
        ]

    def clean(self):
        if self.from_user == self.to_user:
            raise ValidationError("Users cannot send friend requests to themselves.")
        
        if Friendship.objects.filter(from_user=self.from_user, to_user=self.to_user).exists():
            raise ValidationError("You have already sent a request to this user.")

        if Friendship.objects.filter(from_user=self.to_user, to_user=self.from_user).exists():
            raise ValidationError("This user has already sent you a friends request.")
        
    def save(self, *args, **kwargs):
        ids_sorted = sorted([self.from_user_id, self.to_user_id], reverse=True)
        self.users_hash = f"{ids_sorted[0]}_{ids_sorted[1]}"
        super().save(*args, **kwargs)

    def get_other_user(self, user):
        if user == self.to_user:
            return self.from_user
        if user == self.from_user:
            return self.to_user
        
    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"