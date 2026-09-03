from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

from .models import Activity


@login_required
def timer(request):
    user = request.user

    activities = Activity.objects.filter(
        user=user
    ).order_by('-start_time')

    total_minutes = activities.aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0

    total_hours = round(total_minutes / 60, 2)

    task_name = request.session.get(
        'current_task_name',
        'No Task Selected'
    )

    current_activity_id = request.session.get(
        'current_activity_id'
    )

    context = {
        'username': user.username,
        'task_name': task_name,
        'activities': activities,
        'total_minutes': total_minutes,
        'total_hours': total_hours,
        'current_activity_id': current_activity_id,
    }

    return render(
        request,
        'pomodoro/index.html',
        context
    )