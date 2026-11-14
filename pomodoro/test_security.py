"""CSRF tests for the timer API that static/js/timer.js calls (CS50W Lecture 8)."""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import TimerSession

PASSWORD = 'Str0ng-pass-2026'


class TimerCsrfTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', PASSWORD)
        self.client = Client(enforce_csrf_checks=True)
        self.client.login(username='alice', password=PASSWORD)
        # timer.js reads this token from the page's <meta name="csrf-token">
        page = self.client.get(reverse('home'))
        self.token = page.cookies['csrftoken'].value

    def test_page_exposes_token_for_javascript(self):
        self.assertContains(self.client.get(reverse('home')), 'name="csrf-token"')

    def test_timer_start_without_token_rejected(self):
        response = self.client.post(reverse('timer_start'), {'mode': 'focus'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(TimerSession.objects.count(), 0)

    def test_timer_start_with_token_accepted(self):
        response = self.client.post(reverse('timer_start'), {
            'mode': 'focus', 'csrfmiddlewaretoken': self.token,
        })
        self.assertEqual(response.status_code, 200)

    def test_timer_finish_without_token_rejected(self):
        session = TimerSession.objects.create(
            user=self.user, mode='focus', start_time='2026-01-01T00:00:00Z')
        response = self.client.post(reverse('timer_finish'), {
            'session_id': session.id, 'seconds': 60,
        })
        self.assertEqual(response.status_code, 403)
        session.refresh_from_db()
        self.assertIsNone(session.end_time)

    def test_end_task_without_token_rejected(self):
        response = self.client.post(reverse('end_task'))
        self.assertEqual(response.status_code, 403)
