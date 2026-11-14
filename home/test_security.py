"""Security tests (CS50W Lecture 8): passwords, CSRF, XSS, SQL injection, sessions.

These only *check* the protections the project already has - nothing here changes the app.
"""
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from pomodoro.models import Activity

from .models import Profile

PASSWORD = 'Str0ng-pass-2026'
ATTACK = '"><script>alert(1)</script>'


def make_user(username='alice', email='alice@example.com'):
    user = User.objects.create_user(username=username, email=email, password=PASSWORD)
    Profile.objects.create(user=user, status='student')
    return user


class PasswordStorageTests(TestCase):
    """Lecture: never store passwords in plain text, store a one-way hash."""

    def test_registered_password_is_hashed(self):
        self.client.post(reverse('register'), {
            'username': 'carol', 'email': 'carol@example.com',
            'password': PASSWORD, 'status': 'student',
        })
        stored = User.objects.get(username='carol').password
        self.assertNotIn(PASSWORD, stored)
        identify_hasher(stored)  # raises ValueError if it is not a real Django hash

    def test_same_password_gets_different_hashes(self):
        # Each hash has its own random salt, so equal passwords look different
        a, b = make_user('a', 'a@example.com'), make_user('b', 'b@example.com')
        self.assertNotEqual(a.password, b.password)

    def test_password_never_shown_in_profile_page(self):
        make_user()
        self.client.login(username='alice', password=PASSWORD)
        page = self.client.get(reverse('profile'))
        self.assertNotContains(page, PASSWORD)
        self.assertNotContains(page, User.objects.get(username='alice').password)


class CsrfProtectionTests(TestCase):
    """Lecture: a POST without the secret CSRF token must be rejected."""

    def setUp(self):
        make_user()
        self.client = Client(enforce_csrf_checks=True)

    def test_register_without_token_rejected(self):
        response = self.client.post(reverse('register'), {
            'username': 'x', 'email': 'x@example.com', 'password': PASSWORD, 'status': 'student',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='x').exists())

    def test_login_without_token_rejected(self):
        response = self.client.post(reverse('login'), {
            'email': 'alice@example.com', 'password': PASSWORD, 'task_name': 't',
        })
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_profile_change_without_token_rejected(self):
        self.client.login(username='alice', password=PASSWORD)
        response = self.client.post(reverse('profile'), {
            'username': 'hacked', 'email': 'evil@example.com',
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.get(pk=1).username, 'alice')

    def test_login_form_contains_csrf_token(self):
        self.assertContains(self.client.get(reverse('login')), 'csrfmiddlewaretoken')

    def test_register_form_contains_csrf_token(self):
        self.assertContains(self.client.get(reverse('register')), 'csrfmiddlewaretoken')


class XssTests(TestCase):
    """Lecture: user input shown on a page must be escaped, or it can run as JavaScript."""

    def test_username_is_escaped_on_timer_and_profile_pages(self):
        make_user(username=ATTACK)
        self.client.login(username=ATTACK, password=PASSWORD)
        for url in (reverse('home'), reverse('profile')):
            with self.subTest(url=url):
                page = self.client.get(url)
                self.assertNotContains(page, '<script>alert(1)</script>')

    def test_task_name_and_description_are_escaped(self):
        user = make_user()
        Activity.objects.create(
            user=user, task_name=ATTACK, task_description=ATTACK,
            start_time='2026-01-01T00:00:00Z', end_time='2026-01-01T00:10:00Z',
            duration_minutes=10,
        )
        self.client.login(username='alice', password=PASSWORD)
        page = self.client.get(reverse('home'))
        self.assertNotContains(page, '<script>alert(1)</script>')
        self.assertContains(page, '&lt;script&gt;')

    def test_task_name_entered_at_login_is_escaped(self):
        make_user()
        self.client.post(reverse('login'), {
            'email': 'alice@example.com', 'password': PASSWORD, 'task_name': ATTACK,
        })
        page = self.client.get(reverse('home'))
        self.assertNotContains(page, '<script>alert(1)</script>')


class SqlInjectionTests(TestCase):
    """Lecture: Django's ORM sends user input as data, never as SQL code."""

    def setUp(self):
        make_user()

    def test_login_with_sql_in_email_fails(self):
        for email in ["' OR '1'='1", "alice@example.com' --", "x' OR 1=1; --"]:
            with self.subTest(email=email):
                response = self.client.post(reverse('login'), {
                    'email': email, 'password': "' OR '1'='1", 'task_name': 't',
                })
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_sql_in_username_is_stored_as_plain_text(self):
        payload = "bob'); DROP TABLE auth_user; --"
        self.client.post(reverse('register'), {
            'username': payload, 'email': 'bob@example.com',
            'password': PASSWORD, 'status': 'student',
        })
        self.assertTrue(User.objects.filter(username=payload).exists())
        self.assertTrue(User.objects.filter(username='alice').exists())  # table still there


class SessionCookieTests(TestCase):
    def test_session_cookie_cannot_be_read_by_javascript_and_is_samesite(self):
        make_user()
        response = self.client.post(reverse('login'), {
            'email': 'alice@example.com', 'password': PASSWORD, 'task_name': 't',
        })
        cookie = response.cookies['sessionid']
        self.assertTrue(cookie['httponly'])     # JavaScript (and XSS) cannot read it
        self.assertEqual(cookie['samesite'], 'Lax')  # not sent on cross-site POST/img requests


class LoginRequiredTests(TestCase):
    def test_pages_and_apis_redirect_anonymous_users_to_login(self):
        for method, name in [('get', 'home'), ('get', 'profile'), ('post', 'end_task'),
                             ('post', 'timer_start'), ('post', 'timer_finish')]:
            with self.subTest(url=name):
                response = getattr(self.client, method)(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])
