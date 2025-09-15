from django.contrib import admin
from .models import Thread


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_participants', 'created_at')
    search_fields = ('name', 'participants__username')
    filter_horizontal = ('participants',)

    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = "Participants"