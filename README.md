# Pomodoro-Django

Pomodoro timer website built with Django (port of last year's PHP project).
Register, log in with email, start a task, use the Focus / Short Break / Long Break timer,
and see the activity history. Data is saved in SQLite and can be viewed in the Django admin.

## Run the website

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # for /admin/
python manage.py runserver
```

Open http://127.0.0.1:8000/

With Docker instead: `docker compose up` (see `Dockerfile`, `docker-compose.yml`).

## What came from the CS50W videos

| Video topic | Where it is in this repo |
|---|---|
| Lecture 7: unit tests (`TestCase`, test client) | `home/tests.py`, `pomodoro/tests.py` |
| Lecture 7: Selenium | `pomodoro/test_browser.py` (Pomodoro app) and `lecture7_examples/test_counter.py` (the lecture's counter) |
| Lecture 7: `assert`, `is_prime`, `unittest` | `lecture7_examples/` |
| Lecture 7: CI/CD with GitHub Actions | `.github/workflows/ci.yml` |
| Lecture 7: Docker | `Dockerfile`, `docker-compose.yml`, `.dockerignore` |
| Lecture 8: security (passwords, CSRF, XSS, SQL injection, cookies) | `home/test_security.py`, `pomodoro/test_security.py` |
| Lecture 8: XSS and CSRF demos, caching | `lecture8_examples/` (separate mini Django project) |

## Run the tests

```bash
pip install -r requirements-dev.txt     # adds Selenium for the browser tests
python manage.py test                   # Pomodoro app (browser tests are skipped if Chrome is missing)

cd lecture7_examples && python -m unittest discover -v
cd lecture8_examples && python manage.py test
```

GitHub Actions runs all of these on every push.
