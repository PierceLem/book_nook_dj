from django.contrib import admin
from django.urls import path, include
from books.views import search_books

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),
    path('api/v1/', include('djoser.urls.authtoken')),
    path("search-books/", search_books, name="search_books"),
]
