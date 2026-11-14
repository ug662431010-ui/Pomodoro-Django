"""Browser tests with Selenium (the second half of CS50W Lecture 7).

Unlike the tests in tests.py (which call the views directly), these open the real
site in a real Chrome window, so they also test the HTML and static/js/timer.js.

They are skipped automatically when Selenium or Chrome is not installed, so
`python manage.py test` still works on any computer.

    pip install -r requirements-dev.txt
"""
import unittest

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:  # selenium is optional
    webdriver = None

PASSWORD = 'Str0ng-pass-2026'


@unittest.skipIf(webdriver is None, 'selenium is not installed')
class TimerBrowserTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument('--headless=new')  # no window; remove this line to watch the test
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1280,900')
        try:
            cls.driver = webdriver.Chrome(options=options)
        except Exception as error:  # Chrome / driver missing
            super().tearDownClass()
            raise unittest.SkipTest(f'Chrome is not available: {error}')
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        User.objects.create_user('alice', 'alice@example.com', PASSWORD)

    def login(self):
        d = self.driver
        d.get(f'{self.live_server_url}/login/')
        d.find_element(By.ID, 'email').send_keys('alice@example.com')
        d.find_element(By.ID, 'password').send_keys(PASSWORD)
        d.find_element(By.ID, 'task_name').send_keys('Browser test task')
        d.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
        WebDriverWait(d, 5).until(lambda drv: drv.find_element(By.ID, 'timerDisplay'))

    def display(self):
        return self.driver.find_element(By.ID, 'timerDisplay').text

    def test_login_shows_task_and_default_timer(self):
        self.login()
        self.assertEqual(self.display(), '25:00')
        self.assertIn('Browser test task', self.driver.page_source)

    def test_mode_buttons_change_the_timer(self):
        self.login()
        for button_id, expected, label in [
            ('breakBtn', '05:00', 'Short Break'),
            ('longBtn', '15:00', 'Long Break'),
            ('focusBtn', '25:00', 'Focus Mode'),
        ]:
            with self.subTest(button=button_id):
                self.driver.find_element(By.ID, button_id).click()
                self.assertEqual(self.display(), expected)
                self.assertEqual(self.driver.find_element(By.ID, 'statusLabel').text, label)

    def test_timer_counts_down(self):
        self.login()
        self.driver.find_element(By.CSS_SELECTOR, '.control-buttons .start').click()
        WebDriverWait(self.driver, 5).until(lambda drv: self.display() != '25:00')
        self.assertEqual(self.display()[:3], '24:')

    def test_wrong_password_shows_error(self):
        d = self.driver
        d.get(f'{self.live_server_url}/login/')
        d.find_element(By.ID, 'email').send_keys('alice@example.com')
        d.find_element(By.ID, 'password').send_keys('wrong-password')
        d.find_element(By.ID, 'task_name').send_keys('x')
        d.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
        self.assertIn('Invalid email or password', d.page_source)

    def test_password_toggle_on_login_page(self):
        d = self.driver
        d.get(f'{self.live_server_url}/login/')
        field = d.find_element(By.ID, 'password')
        self.assertEqual(field.get_attribute('type'), 'password')
        d.find_element(By.CLASS_NAME, 'toggle-password').click()
        self.assertEqual(field.get_attribute('type'), 'text')
