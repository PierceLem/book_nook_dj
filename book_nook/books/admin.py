from django.contrib import admin
from .models import BookReview, Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'id')

@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'created_at')
    search_fields = ('book', 'user__username', 'review')
    list_filter = ('created_at', 'user')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
