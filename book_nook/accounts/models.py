from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db.models.functions import Least, Greatest
from django.db.models import Q, F
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
    bio = models.TextField(null=True, blank=True)

    '''User settings fields'''
    friend_request_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    auto_accept_friend_requests = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username
    

class Friendship(models.Model):
    from_user = models.ForeignKey(NookUser, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(NookUser, related_name='friend_requests_received', on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(from_user=F('to_user')),
                name="prevent_self_friendship"
            ),
            
            models.UniqueConstraint(
                Least("from_user", "to_user"),
                Greatest("from_user", "to_user"),
                name="unique_symmetric_friendship"
            )
        ]

    def clean(self):
        if self.from_user == self.to_user:
            raise ValidationError("Users cannot send friend requests to themselves.")
        
        friendship = Friendship.objects.filter(
            Q(from_user=self.from_user, to_user=self.to_user) |
            Q(from_user=self.to_user, to_user=self.from_user)
        ).exclude(pk=self.pk).first()

        if friendship:
            if friendship.accepted == True:
                raise ValidationError("You are already friends with this user.")
            else:
                if friendship.from_user == self.from_user:
                    raise ValidationError("You have already sent a request to this user.")
                else:
                    raise ValidationError("This user has already sent you a friends request.")

    def get_other_user(self, user):
        if user == self.to_user:
            return self.from_user
        if user == self.from_user:
            return self.to_user
        
    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.accepted})"