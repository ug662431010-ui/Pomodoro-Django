from django.contrib import admin
from django.db.models import Q, Sum

from .models import Activity, TimerSession


def minutes_text(seconds):
    """Show seconds as minutes with one decimal (e.g. 90 -> 1.5)."""
    return round((seconds or 0) / 60, 1)


class TimerSessionInline(admin.TabularInline):
    """Timer runs shown inside the page of one activity (read only)."""

    model = TimerSession
    extra = 0
    can_delete = False
    fields = ('mode', 'start_time', 'end_time', 'duration_seconds', 'completed')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        'task_name', 'user', 'start_time', 'end_time', 'duration_minutes',
        'focus_minutes', 'short_break_minutes', 'long_break_minutes',
    )
    list_filter = ('user',)
    search_fields = ('task_name', 'user__username')
    inlines = [TimerSessionInline]

    def get_queryset(self, request):
        # Add up the seconds of each mode for every activity
        return super().get_queryset(request).annotate(
            _focus=Sum('sessions__duration_seconds', filter=Q(sessions__mode='focus')),
            _short=Sum('sessions__duration_seconds', filter=Q(sessions__mode='short_break')),
            _long=Sum('sessions__duration_seconds', filter=Q(sessions__mode='long_break')),
        )

    @admin.display(description='Focus (min)', ordering='_focus')
    def focus_minutes(self, obj):
        return minutes_text(obj._focus)

    @admin.display(description='Short break (min)', ordering='_short')
    def short_break_minutes(self, obj):
        return minutes_text(obj._short)

    @admin.display(description='Long break (min)', ordering='_long')
    def long_break_minutes(self, obj):
        return minutes_text(obj._long)


@admin.register(TimerSession)
class TimerSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'mode', 'activity', 'start_time', 'end_time', 'time_used', 'status')
    list_filter = ('mode', 'completed', 'user')
    search_fields = ('user__username', 'activity__task_name')

    @admin.display(description='Time used')
    def time_used(self, obj):
        minutes, seconds = divmod(obj.duration_seconds, 60)
        return f'{minutes:02d}:{seconds:02d}'

    @admin.display(description='Status')
    def status(self, obj):
        if obj.completed:
            return 'Completed'
        if obj.end_time:
            return 'Stopped early'
        return 'Running / not finished'
