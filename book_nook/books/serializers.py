from rest_framework import serializers


class BookSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField(source="volumeInfo.title", default="No Title")
    authors = serializers.ListField(source="volumeInfo.authors", default=["Unknown"])
    description = serializers.CharField(source="volumeInfo.description", required=False, allow_blank=True)
    published_date = serializers.CharField(source="volumeInfo.publishedDate", default="N/A")
    thumbnail = serializers.CharField(source="volumeInfo.imageLinks.thumbnail", default="")
