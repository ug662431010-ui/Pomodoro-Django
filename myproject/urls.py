from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),      # login, register, logout, about, profile
    path('', include('pomodoro.urls')),  # home (timer) and end-task
]
