from django.contrib import admin
from django.urls import path, include
from books.views import SearchBooks, CreateOrEditReview, BookReviewList, UserBookshelf, ToggleSaveBook, DeleteReview

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),
    path('api/v1/', include('djoser.urls.authtoken')),
    path("search-books/", SearchBooks.as_view(), name="search-books"),
    path('add-review/', CreateOrEditReview.as_view(), name='add-review'),
    path('delete-review/<int:review_id>/', DeleteReview.as_view(), name='delete-review'),
    path("reviews/<str:book_id>/", BookReviewList.as_view(), name="book-reviews"),
    path('bookshelf/', UserBookshelf.as_view(), name='bookshelf'),
    path("toggle-save-book/", ToggleSaveBook.as_view(), name="toggle-save-book"),
]