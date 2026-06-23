from django.contrib import admin
from .models import Thread, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('message_id', 'sender', 'get_content', 'created_at')
    fields = ('message_id', 'sender', 'get_content', 'created_at')

    def message_id(self, obj):
        return obj.id
    message_id.short_description = "ID"

    def get_content(self, obj):
        from django.utils.html import format_html
        style = "max-width: 300px; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
        
        if obj.content:
            return format_html('<span style="{}">{}</span>', style, obj.content)
        elif obj.book:
            return format_html('<span style="{}">{}</span>', style, obj.book)
        elif obj.thread_update:
            return format_html('<span style="{}">{}</span>', style, obj.thread_update)
        return "-"
    get_content.short_description = "Content"

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_participants', 'created_at')
    search_fields = ('name', 'participants__username')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]

    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = "Participants"