from .models import Book


def get_or_create_book(book_data):
    book_id = book_data.get("book_id")
    if not book_id:
        return None

    book, created = Book.objects.get_or_create(id=book_id, defaults={
        "title": book_data.get("title", "Unknown Title"),
        "authors": book_data.get("authors", []),
        "description": book_data.get("description", ""),
        "thumbnail": book_data.get("thumbnail", ""),
    })
    return book