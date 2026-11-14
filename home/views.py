from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils import timezone

from pomodoro.models import Activity

from .forms import ProfileForm, RegisterForm


def login_view(request):
    """Login with email + password and start a new task (like login.php)."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        task_name = request.POST.get('task_name', '').strip()
        task_description = request.POST.get('task_description', '').strip()

        account = User.objects.filter(email__iexact=email).first()

        if account is None:
            messages.error(request, 'No account found with that email.')
        else:
            user = authenticate(request, username=account.username, password=password)
            if user is None:
                messages.error(request, 'Invalid email or password.')
            else:
                login(request, user)

                # Save the new task in the database (visible in the admin site)
                activity = Activity.objects.create(
                    user=user,
                    task_name=task_name,
                    task_description=task_description,
                    start_time=timezone.now(),
                )
                request.session['current_task_name'] = task_name
                request.session['current_activity_id'] = activity.id
                return redirect('home')

    return render(request, 'home/login.html')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Registration successful! Please log in to start your Pomodoro.',
            )
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'home/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def about_view(request):
    return render(request, 'home/about.html')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Profile updated successfully! Username changed to: {user.username}',
            )
            return redirect('profile')
    else:
        form = ProfileForm(
            initial={'username': request.user.username, 'email': request.user.email},
            user=request.user,
        )

    return render(request, 'home/profile.html', {'form': form})
