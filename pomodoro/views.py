from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Activity, TimerSession

# Length of each timer mode in seconds (same values as the buttons on the page)
MODE_LENGTH_SECONDS = {
    'focus': 25 * 60,
    'short_break': 5 * 60,
    'long_break': 15 * 60,
}


@login_required
def timer(request):
    """Home page: the Pomodoro timer, current task and activity history (like index.php)."""
    user = request.user

    # Only keep the "current task" if it is really still open
    current_activity_id = request.session.get('current_activity_id')
    if current_activity_id and not Activity.objects.filter(
        id=current_activity_id, user=user, end_time__isnull=True
    ).exists():
        request.session.pop('current_activity_id', None)
        request.session.pop('current_task_name', None)
        current_activity_id = None

    activities = Activity.objects.filter(user=user).order_by('-start_time')

    total_minutes = activities.aggregate(total=Sum('duration_minutes'))['total'] or 0
    total_hours = round(total_minutes / 60, 2)

    context = {
        'username': user.username,
        'task_name': request.session.get('current_task_name', 'No Task Selected'),
        'activities': activities,
        'total_minutes': total_minutes,
        'total_hours': total_hours,
        'current_activity_id': current_activity_id,
    }
    return render(request, 'pomodoro/index.html', context)


@login_required
@require_POST
def end_task(request):
    """End the current task and save its end time and duration (like end_task.php)."""
    activity = Activity.objects.filter(
        id=request.session.get('current_activity_id'),
        user=request.user,
        end_time__isnull=True,
    ).first()

    if activity:
        end_time = timezone.now()
        duration_minutes = round((end_time - activity.start_time).total_seconds() / 60)

        activity.end_time = end_time
        activity.duration_minutes = duration_minutes
        activity.save()

        messages.success(
            request, f'Task completed! Time spent: {duration_minutes} minutes.'
        )
    else:
        messages.error(
            request, 'Error: Cannot find active task or task already ended.'
        )

    request.session.pop('current_task_name', None)
    request.session.pop('current_activity_id', None)
    return redirect('home')


@login_required
@require_POST
def timer_start(request):
    """Called by the page when the user starts a timer: save which mode is being used."""
    mode = request.POST.get('mode')
    if mode not in MODE_LENGTH_SECONDS:
        return JsonResponse({'error': 'Invalid mode.'}, status=400)

    # Link the session to the task that is still open (if there is one)
    activity = Activity.objects.filter(
        id=request.session.get('current_activity_id'),
        user=request.user,
        end_time__isnull=True,
    ).first()

    session = TimerSession.objects.create(
        user=request.user,
        activity=activity,
        mode=mode,
        start_time=timezone.now(),
    )
    return JsonResponse({'id': session.id})


@login_required
@require_POST
def timer_finish(request):
    """Called by the page when a timer run ends (finished, reset, mode switched or page closed)."""
    try:
        session_id = int(request.POST.get('session_id', ''))
        seconds = int(request.POST.get('seconds', 0))
    except ValueError:
        return JsonResponse({'error': 'Invalid data.'}, status=400)

    session = TimerSession.objects.filter(
        id=session_id, user=request.user, end_time__isnull=True
    ).first()
    if session is None:
        return JsonResponse({'error': 'Session not found.'}, status=404)

    completed = request.POST.get('completed') == '1'

    # Never trust the browser: keep seconds between 0 and the length of the mode
    seconds = max(0, min(seconds, MODE_LENGTH_SECONDS[session.mode]))

    if seconds == 0 and not completed:
        session.delete()  # accidental click: nothing was timed, so do not keep it
    else:
        session.end_time = timezone.now()
        session.duration_seconds = seconds
        session.completed = completed
        session.save()

    return JsonResponse({'ok': True})
