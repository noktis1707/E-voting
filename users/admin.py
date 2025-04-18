from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'id', 'full_name', 'email', 'is_staff', 'avatar'
    )
    fieldsets = (
        (None, {'fields': ('username', 'password', 'first_name', 'last_name', 'email', 'avatar',
                            'is_active', 'is_staff', 'full_name', 's_n', 'born', 'groups')}), 
    )

admin.site.register(User, CustomUserAdmin)
