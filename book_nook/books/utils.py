from .models import Book

def get_or_create_book(book_id):
    if not book_id:
        raise ValueError("book_id is required")
    
    book, created = Book.objects.get_or_create(book_id=book_id)
    return book