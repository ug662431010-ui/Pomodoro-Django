from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from pomodoro.models import Activity

from .forms import ProfileForm, RegisterForm
from .models import Profile

GOOD_PASSWORD = 'Str0ng-pass-2026'


def make_user(username='alice', email='alice@example.com', password=GOOD_PASSWORD):
    """Small helper: create a user + profile the same way the register form does."""
    user = User.objects.create_user(username=username, email=email, password=password)
    Profile.objects.create(user=user, status='student')
    return user


def messages_of(response):
    return [str(m) for m in response.context['messages']]


class ProfileModelTests(TestCase):
    def test_str(self):
        user = make_user()
        self.assertEqual(str(user.profile), 'alice (student)')

    def test_deleting_user_deletes_profile(self):
        user = make_user()
        user.delete()
        self.assertEqual(Profile.objects.count(), 0)


class RegisterFormTests(TestCase):
    def data(self, **changes):
        data = {
            'username': 'bob',
            'email': 'bob@example.com',
            'password': GOOD_PASSWORD,
            'status': 'student',
        }
        data.update(changes)
        return data

    def test_valid_form_creates_user_and_profile(self):
        form = RegisterForm(self.data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.check_password(GOOD_PASSWORD))
        self.assertEqual(user.profile.status, 'student')

    def test_password_is_hashed(self):
        user = RegisterForm(self.data())
        user.is_valid()
        saved = user.save()
        self.assertNotEqual(saved.password, GOOD_PASSWORD)

    def test_duplicate_username_rejected_ignoring_case(self):
        make_user(username='Bob', email='other@example.com')
        form = RegisterForm(self.data(username='bob'))
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_duplicate_email_rejected_ignoring_case(self):
        make_user(username='someone', email='BOB@example.com')
        form = RegisterForm(self.data())
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_status_rejected(self):
        form = RegisterForm(self.data(status='hacker'))
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_invalid_email_rejected(self):
        form = RegisterForm(self.data(email='not-an-email'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ProfileFormTests(TestCase):
    def setUp(self):
        self.alice = make_user('alice', 'alice@example.com')
        self.bob = make_user('bob', 'bob@example.com')

    def test_user_can_keep_own_username_and_email(self):
        form = ProfileForm({'username': 'alice', 'email': 'alice@example.com'}, user=self.alice)
        self.assertTrue(form.is_valid(), form.errors)

    def test_cannot_take_other_users_username(self):
        form = ProfileForm({'username': 'Bob', 'email': 'alice@example.com'}, user=self.alice)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_cannot_take_other_users_email(self):
        form = ProfileForm({'username': 'alice', 'email': 'bob@example.com'}, user=self.alice)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_save_updates_user(self):
        form = ProfileForm({'username': 'alice2', 'email': 'new@example.com'}, user=self.alice)
        self.assertTrue(form.is_valid())
        form.save()
        self.alice.refresh_from_db()
        self.assertEqual((self.alice.username, self.alice.email), ('alice2', 'new@example.com'))


class RegisterViewTests(TestCase):
    def test_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/register.html')

    def test_successful_register_redirects_to_login(self):
        response = self.client.post(reverse('register'), {
            'username': 'carol', 'email': 'carol@example.com',
            'password': GOOD_PASSWORD, 'status': 'lecturer',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='carol').exists())



class LoginViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def login(self, **changes):
        data = {
            'email': 'alice@example.com', 'password': GOOD_PASSWORD,
            'task_name': 'Study Django', 'task_description': 'Chapter 7',
        }
        data.update(changes)
        return self.client.post(reverse('login'), data)

    def test_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/login.html')

    def test_successful_login_starts_task(self):
        response = self.login()
        self.assertRedirects(response, reverse('home'))
        activity = Activity.objects.get(user=self.user)
        self.assertEqual(activity.task_name, 'Study Django')
        self.assertIsNone(activity.end_time)
        self.assertEqual(self.client.session['current_activity_id'], activity.id)

    def test_email_is_case_insensitive(self):
        self.assertRedirects(self.login(email='ALICE@Example.com'), reverse('home'))

    def test_unknown_email_is_rejected(self):
        response = self.login(email='nobody@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(messages_of(response), ['No account found with that email.'])
        self.assertEqual(Activity.objects.count(), 0)

    def test_wrong_password(self):
        response = self.login(password='wrong')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(messages_of(response), ['Invalid email or password.'])
        self.assertEqual(Activity.objects.count(), 0)



class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username='alice', password=GOOD_PASSWORD)

    def test_logout_redirects_and_logs_out(self):
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_when_not_logged_in_is_fine(self):
        self.client.logout()
        self.assertRedirects(self.client.get(reverse('logout')), reverse('login'))


class AboutViewTests(TestCase):
    def test_public(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pomodoro Technique')


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_shows_current_values(self):
        self.client.login(username='alice', password=GOOD_PASSWORD)
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'alice@example.com')

    def test_update_profile(self):
        self.client.login(username='alice', password=GOOD_PASSWORD)
        response = self.client.post(
            reverse('profile'), {'username': 'alice2', 'email': 'alice2@example.com'}
        )
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'alice2')

    def test_duplicate_email_rejected(self):
        make_user('bob', 'bob@example.com')
        self.client.login(username='alice', password=GOOD_PASSWORD)
        response = self.client.post(
            reverse('profile'), {'username': 'alice', 'email': 'bob@example.com'}
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'alice@example.com')
