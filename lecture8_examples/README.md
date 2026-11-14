# Lecture 8 demo (scalability + security) - separate from the Pomodoro project

    pip install Django
    python manage.py test        # proves each demo
    python manage.py migrate     # once, creates the session table used by the bank demo
    python manage.py runserver   # then try the URLs below

| URL | What to try |
|---|---|
| /vulnerable/<script>alert('hacked')</script> | XSS: the script runs (bad) |
| /safe/<script>alert('hacked')</script> | The same text is shown as text (good) |
| /bank/ | open first (creates your session), then open `attacks/link.html` and click, and reload /bank/ |
| attacks/form.html | POST without CSRF token -> 403 Forbidden |
| /clock/ | reload several times: the time stays the same for 60 seconds (cache) |
