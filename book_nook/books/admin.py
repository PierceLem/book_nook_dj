from django.contrib import admin
from .models import BookReview, ReviewLike, BookLike, Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('book_id',)

@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'user', 'created_at')
    search_fields = ('book_id', 'user__username', 'review')
    list_filter = ('created_at', 'user')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ('review', 'created_at')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(BookLike)
class BookLikeAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'user', 'created_at')
    search_fields = ('book_id', 'user__username')
    list_filter = ('created_at', 'user')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
