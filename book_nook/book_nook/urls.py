from django.contrib import admin
from django.urls import path, include
from books.views import SearchBooks, CreateReview, BookReviewList, ToggleBookLike, ToggleReviewLike

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),
    path('api/v1/', include('djoser.urls.authtoken')),
    path("search-books/", SearchBooks.as_view(), name="search-books"),
    path('add-review/', CreateReview.as_view(), name='add-review'),
    path("reviews/<str:book_id>/", BookReviewList.as_view(), name="book-reviews"),
    path('like-book/<str:book_id>/', ToggleBookLike.as_view(), name='like-book'),
    path('like-review/<str:review_id>/', ToggleReviewLike.as_view(), name='like-review'),
]
