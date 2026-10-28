from django.urls import path

from . import views

urlpatterns = [
    path('', views.timer, name='home'),
    path('end-task/', views.end_task, name='end_task'),
    path('timer/start/', views.timer_start, name='timer_start'),
    path('timer/finish/', views.timer_finish, name='timer_finish'),
]
