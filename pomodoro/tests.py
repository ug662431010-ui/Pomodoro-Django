from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Activity, TimerSession
from .views import MODE_LENGTH_SECONDS


def make_user(username='alice'):
    return User.objects.create_user(
        username=username, email=f'{username}@example.com', password='Str0ng-pass-2026'
    )


class ModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_activity_str(self):
        activity = Activity.objects.create(
            user=self.user, task_name='Read chapter', start_time=timezone.now()
        )
        self.assertEqual(str(activity), 'Read chapter')

    def test_activity_is_open_until_end_time_set(self):
        activity = Activity.objects.create(
            user=self.user, task_name='x', start_time=timezone.now()
        )
        self.assertIsNone(activity.end_time)
        self.assertIsNone(activity.duration_minutes)

    def test_timer_session_defaults_and_str(self):
        session = TimerSession.objects.create(
            user=self.user, mode='short_break', start_time=timezone.now()
        )
        self.assertEqual(session.duration_seconds, 0)
        self.assertFalse(session.completed)
        self.assertEqual(str(session), 'Short Break (5m) - alice')

    def test_timer_sessions_newest_first(self):
        now = timezone.now()
        old = TimerSession.objects.create(user=self.user, mode='focus', start_time=now - timedelta(hours=1))
        new = TimerSession.objects.create(user=self.user, mode='focus', start_time=now)
        self.assertEqual(list(TimerSession.objects.all()), [new, old])

    def test_deleting_activity_deletes_its_sessions(self):
        activity = Activity.objects.create(user=self.user, task_name='x', start_time=timezone.now())
        TimerSession.objects.create(
            user=self.user, activity=activity, mode='focus', start_time=timezone.now()
        )
        activity.delete()
        self.assertEqual(TimerSession.objects.count(), 0)

    def test_mode_lengths(self):
        self.assertEqual(MODE_LENGTH_SECONDS, {'focus': 1500, 'short_break': 300, 'long_break': 900})


class TimerPageTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username='alice', password='Str0ng-pass-2026')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_no_task_selected(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Task Selected')
        self.assertNotContains(response, 'End Current Task')

    def test_shows_current_task_and_end_button(self):
        activity = Activity.objects.create(user=self.user, task_name='Write tests', start_time=timezone.now())
        session = self.client.session
        session['current_activity_id'] = activity.id
        session['current_task_name'] = 'Write tests'
        session.save()
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Write tests')
        self.assertContains(response, 'End Current Task')

    def test_stale_session_task_is_forgotten(self):
        ended = Activity.objects.create(
            user=self.user, task_name='Old', start_time=timezone.now(), end_time=timezone.now()
        )
        session = self.client.session
        session['current_activity_id'] = ended.id
        session['current_task_name'] = 'Old'
        session.save()
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'No Task Selected')
        self.assertNotIn('current_activity_id', self.client.session)

    def test_only_own_activities_and_total_minutes(self):
        other = make_user('bob')
        now = timezone.now()
        Activity.objects.create(user=self.user, task_name='mine', start_time=now,
                                end_time=now, duration_minutes=90)
        Activity.objects.create(user=other, task_name='theirs', start_time=now,
                                end_time=now, duration_minutes=500)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['total_minutes'], 90)
        self.assertEqual(response.context['total_hours'], 1.5)
        self.assertContains(response, 'mine')
        self.assertNotContains(response, 'theirs')


class EndTaskTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username='alice', password='Str0ng-pass-2026')
        self.activity = Activity.objects.create(
            user=self.user, task_name='Task', start_time=timezone.now() - timedelta(minutes=10)
        )
        session = self.client.session
        session['current_activity_id'] = self.activity.id
        session['current_task_name'] = 'Task'
        session.save()

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse('end_task')).status_code, 405)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse('end_task'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_end_task_saves_end_time_and_duration(self):
        response = self.client.post(reverse('end_task'))
        self.assertRedirects(response, reverse('home'))
        self.activity.refresh_from_db()
        self.assertIsNotNone(self.activity.end_time)
        self.assertEqual(self.activity.duration_minutes, 10)
        self.assertNotIn('current_activity_id', self.client.session)

    def test_end_task_twice_shows_error(self):
        self.client.post(reverse('end_task'))
        response = self.client.post(reverse('end_task'), follow=True)
        messages = [str(m) for m in response.context['messages']]
        self.assertTrue(any('Cannot find active task' in m for m in messages))

    def test_cannot_end_another_users_task(self):
        other = make_user('bob')
        theirs = Activity.objects.create(user=other, task_name='theirs', start_time=timezone.now())
        session = self.client.session
        session['current_activity_id'] = theirs.id
        session.save()
        self.client.post(reverse('end_task'))
        theirs.refresh_from_db()
        self.assertIsNone(theirs.end_time)


class TimerApiTests(TestCase):
    """timer_start / timer_finish are called by static/js/timer.js."""

    def setUp(self):
        self.user = make_user()
        self.client.login(username='alice', password='Str0ng-pass-2026')

    def start(self, mode='focus'):
        return self.client.post(reverse('timer_start'), {'mode': mode})

    def finish(self, session_id, seconds, completed='0'):
        return self.client.post(reverse('timer_finish'), {
            'session_id': session_id, 'seconds': seconds, 'completed': completed,
        })

    def test_both_endpoints_require_post(self):
        self.assertEqual(self.client.get(reverse('timer_start')).status_code, 405)
        self.assertEqual(self.client.get(reverse('timer_finish')).status_code, 405)

    def test_both_endpoints_require_login(self):
        self.client.logout()
        self.assertEqual(self.start().status_code, 302)
        self.assertEqual(self.finish(1, 10).status_code, 302)

    def test_start_creates_session(self):
        response = self.start('long_break')
        self.assertEqual(response.status_code, 200)
        session = TimerSession.objects.get(id=response.json()['id'])
        self.assertEqual((session.user, session.mode), (self.user, 'long_break'))
        self.assertIsNone(session.end_time)

    def test_start_invalid_mode(self):
        self.assertEqual(self.start('nap').status_code, 400)
        self.assertEqual(TimerSession.objects.count(), 0)

    def test_start_links_to_open_task(self):
        activity = Activity.objects.create(user=self.user, task_name='t', start_time=timezone.now())
        session = self.client.session
        session['current_activity_id'] = activity.id
        session.save()
        sid = self.start().json()['id']
        self.assertEqual(TimerSession.objects.get(id=sid).activity, activity)

    def test_start_without_task_has_no_activity(self):
        sid = self.start().json()['id']
        self.assertIsNone(TimerSession.objects.get(id=sid).activity)

    def test_finish_early_saves_seconds(self):
        sid = self.start().json()['id']
        self.assertEqual(self.finish(sid, 120).status_code, 200)
        session = TimerSession.objects.get(id=sid)
        self.assertEqual(session.duration_seconds, 120)
        self.assertFalse(session.completed)
        self.assertIsNotNone(session.end_time)

    def test_finish_completed(self):
        sid = self.start('short_break').json()['id']
        self.finish(sid, 300, completed='1')
        session = TimerSession.objects.get(id=sid)
        self.assertTrue(session.completed)
        self.assertEqual(session.duration_seconds, 300)

    def test_finish_clamps_seconds_to_mode_length(self):
        sid = self.start('short_break').json()['id']
        self.finish(sid, 99999)
        self.assertEqual(TimerSession.objects.get(id=sid).duration_seconds, 300)

    def test_finish_clamps_negative_seconds(self):
        sid = self.start().json()['id']
        self.finish(sid, 5)  # keep a real row
        sid2 = self.start().json()['id']
        self.finish(sid2, -50, completed='1')
        self.assertEqual(TimerSession.objects.get(id=sid2).duration_seconds, 0)

    def test_finish_with_zero_seconds_deletes_accidental_click(self):
        sid = self.start().json()['id']
        self.finish(sid, 0)
        self.assertFalse(TimerSession.objects.filter(id=sid).exists())

    def test_finish_twice_returns_404(self):
        sid = self.start().json()['id']
        self.finish(sid, 10)
        self.assertEqual(self.finish(sid, 10).status_code, 404)

    def test_cannot_finish_another_users_session(self):
        sid = self.start().json()['id']
        self.client.logout()
        make_user('bob')
        self.client.login(username='bob', password='Str0ng-pass-2026')
        self.assertEqual(self.finish(sid, 10).status_code, 404)
        self.assertIsNone(TimerSession.objects.get(id=sid).end_time)

    def test_finish_with_bad_numbers(self):
        sid = self.start().json()['id']
        for bad in ['abc', '12.5', '']:
            with self.subTest(seconds=bad):
                self.assertEqual(self.finish(sid, bad).status_code, 400)
        self.assertEqual(self.client.post(reverse('timer_finish'), {}).status_code, 400)
