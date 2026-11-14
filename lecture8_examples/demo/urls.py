from django.urls import path

from . import views

urlpatterns = [
    # XSS demo
    path("vulnerable/<path:path>", views.xss_vulnerable),
    path("safe/<path:path>", views.xss_safe),
    # CSRF demo
    path("bank/", views.bank),
    path("bank/unsafe-transfer/", views.transfer_unsafe),
    path("bank/transfer/", views.transfer),
    # Caching demo
    path("clock/", views.clock),
]
