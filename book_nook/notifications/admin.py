from django.contrib import admin
from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'title', 'type', 'content', 'created_at']
    list_filter = ['recipient', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'content']
    ordering = ['recipient', '-created_at']

admin.site.register(Notification, NotificationAdmin)