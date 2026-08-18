from .models import Book


def get_or_create_book(book_data):
    book_id = book_data.get("id")
    if not book_id:
        return None

    book, created = Book.objects.get_or_create(id=book_id, defaults={
        "title": book_data.get("title", "Unknown Title"),
    })
    return book