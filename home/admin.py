from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email')
