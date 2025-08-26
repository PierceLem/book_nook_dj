from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from books.views import SearchBooks, ReviewOptions, BookReviewList, UserBookshelf, ToggleSaveBook
from accounts.views import GoogleLoginView, FriendRequestView, UploadAvatar, FetchFriends


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include("djoser.urls")),
    path('api/v1/', include("djoser.urls.authtoken")),
    path('search-books/', SearchBooks.as_view(), name="search-books"),
    path('review-options/', ReviewOptions.as_view(), name="review-options"),
    path('reviews/<str:book_id>/', BookReviewList.as_view(), name="book-reviews"),
    path('bookshelf/', UserBookshelf.as_view(), name="bookshelf"),
    path('toggle-save-book/', ToggleSaveBook.as_view(), name="toggle-save-book"),
    path('api/auth/google/', GoogleLoginView.as_view(), name="google-login"),
    path('friend-request/', FriendRequestView.as_view(), name="friend-request"),
    path('upload-avatar/', UploadAvatar.as_view(), name="upload-avatar"),
    path('my-friends/', FetchFriends.as_view(), name="my-friends"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)