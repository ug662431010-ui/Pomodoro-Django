# CS50W Lecture 7 - Selenium: open counter.html in a real Chrome and click the buttons
# Needs:  pip install selenium   and Google Chrome.  Run:  python test_counter.py
# (If Selenium or Chrome is missing the tests are skipped instead of failing.)
import os
import pathlib
import unittest

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except ImportError:
    webdriver = None


def file_uri(filename):
    return pathlib.Path(os.path.abspath(filename)).as_uri()


driver = None


def setUpModule():
    global driver
    if webdriver is None:
        raise unittest.SkipTest("selenium is not installed")
    options = Options()
    options.add_argument("--headless=new")   # remove this line to watch the browser
    options.add_argument("--no-sandbox")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as error:
        raise unittest.SkipTest(f"Chrome is not available: {error}")


def tearDownModule():
    if driver is not None:
        driver.quit()


class WebpageTests(unittest.TestCase):
    def setUp(self):
        driver.get(file_uri(os.path.join(os.path.dirname(__file__), "counter.html")))

    def heading(self):
        return driver.find_element(By.TAG_NAME, "h1").text

    def test_title(self):
        self.assertEqual(driver.title, "Counter")

    def test_increase(self):
        driver.find_element(By.ID, "increase").click()
        self.assertEqual(self.heading(), "1")

    def test_decrease(self):
        driver.find_element(By.ID, "decrease").click()
        self.assertEqual(self.heading(), "-1")

    def test_multiple_increase(self):
        increase = driver.find_element(By.ID, "increase")
        for _ in range(3):
            increase.click()
        self.assertEqual(self.heading(), "3")


if __name__ == "__main__":
    unittest.main()
