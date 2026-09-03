from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/pomodoro/')

        return render(request, 'login.html', {
            'error': 'Username or password is incorrect.'
        })

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            return redirect('/login/')

    else:
        form = UserCreationForm()

    return render(request, 'register.html', {
        'form': form
    })


def logout_view(request):
    logout(request)
    return redirect('/login/')