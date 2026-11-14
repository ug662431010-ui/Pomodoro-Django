from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST


# --------------------------------------------------------------------------
# 1) Cross-site scripting (XSS)
#    Anything that comes from the user must not be pasted into HTML as-is.
# --------------------------------------------------------------------------
def xss_vulnerable(request, path):
    """BAD: the URL path goes straight into the HTML.
    Visit /vulnerable/<script>alert('hacked')</script> and the script runs."""
    return HttpResponse(f"<h1>Requested path: {path}</h1>")


def xss_safe(request, path):
    """GOOD: a Django template escapes < > & " ' automatically."""
    return render(request, "echo.html", {"path": path})


# --------------------------------------------------------------------------
# 2) Cross-site request forgery (CSRF)
#    A "bank" that keeps your balance in your session.
# --------------------------------------------------------------------------
def _balance(request):
    return request.session.setdefault("balance", 1000)


def bank(request):
    return render(request, "bank.html", {"balance": _balance(request)})


def transfer_unsafe(request):
    """BAD: a GET request changes data, so a plain link or <img> can trigger it.
    Try attacks/link.html and attacks/image.html."""
    amount = int(request.GET.get("amount", 0))
    request.session["balance"] = _balance(request) - amount
    return HttpResponse(f"Sent {amount}. Balance: {request.session['balance']}")


@require_POST
def transfer(request):
    """GOOD: only POST is accepted, and Django's CsrfViewMiddleware rejects a
    POST that has no valid CSRF token (attacks/form.html gets 403 Forbidden)."""
    amount = int(request.POST.get("amount", 0))
    request.session["balance"] = _balance(request) - amount
    return HttpResponse(f"Sent {amount}. Balance: {request.session['balance']}")


# --------------------------------------------------------------------------
# 3) Caching (scalability)
#    The page is built once, then served from the cache for 60 seconds.
# --------------------------------------------------------------------------
@cache_page(60)
def clock(request):
    return HttpResponse(f"Time when this page was built: {timezone.now().isoformat()}")
