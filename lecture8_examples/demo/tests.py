from urllib.parse import quote

from django.core.cache import cache
from django.test import Client, TestCase

SCRIPT = "<script>alert('hacked')</script>"


class XssTests(TestCase):
    def get(self, prefix):
        return self.client.get(f"/{prefix}/{quote(SCRIPT)}")

    def test_vulnerable_view_puts_the_script_into_the_page(self):
        # This is the bug: the browser would run this script.
        self.assertContains(self.get("vulnerable"), SCRIPT, html=False)

    def test_safe_view_escapes_the_script(self):
        response = self.get("safe")
        self.assertNotContains(response, SCRIPT)
        self.assertContains(response, "&lt;script&gt;")


class CsrfTests(TestCase):
    def test_get_can_change_data_which_is_why_it_is_unsafe(self):
        self.client.get("/bank/")  # creates the session with balance 1000
        self.client.get("/bank/unsafe-transfer/?amount=500")  # just a GET, e.g. a link click
        self.assertEqual(self.client.session["balance"], 500)

    def test_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/bank/")
        response = client.post("/bank/transfer/", {"amount": 500})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(client.session["balance"], 1000)

    def test_post_with_csrf_token_works(self):
        client = Client(enforce_csrf_checks=True)
        page = client.get("/bank/")
        token = page.cookies["csrftoken"].value
        response = client.post("/bank/transfer/", {"amount": 500, "csrfmiddlewaretoken": token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.session["balance"], 500)

    def test_transfer_rejects_get(self):
        self.assertEqual(self.client.get("/bank/transfer/").status_code, 405)


class CacheTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_second_request_is_served_from_cache(self):
        first = self.client.get("/clock/").content
        second = self.client.get("/clock/").content
        self.assertEqual(first, second)  # same timestamp = page was not rebuilt

    def test_cache_header_is_sent(self):
        self.assertIn("max-age=60", self.client.get("/clock/")["Cache-Control"])
