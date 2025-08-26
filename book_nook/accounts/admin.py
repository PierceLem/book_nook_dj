from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token
from .models import NookUser, Friendship


@admin.register(NookUser)
class NookUserAdmin(UserAdmin):
    model = NookUser
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    list_display = ('email', 'username', 'is_staff', 'is_active', 'date_joined', 'is_authenticated')
    search_fields = ('email', 'username')
    ordering = ('email',)
    readonly_fields = ('date_joined',)

    def is_authenticated(self, obj):
        return Token.objects.filter(user=obj).exists()
    
    is_authenticated.short_description = 'Authenticated'
    is_authenticated.boolean = True  

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    readonly_fields = ('users_hash',)
    list_display = ('from_user', 'to_user', 'status', 'users_hash', 'created_at')