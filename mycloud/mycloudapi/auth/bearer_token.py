import time
import urllib.parse as urlparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from mycloud.mycloudapi.auth.selenium_proxy import ProxySelenium
from mycloud.logger import log


WAIT_TIME = 15
START_LOGIN_URL = 'https://start.mycloud.ch'


def open_for_cert():
    with ProxySelenium(headless=False) as driver:
        driver.get('http://mitm.it')
        while any(driver.window_handles):
            pass


def get_bearer_token(user_name: str, password: str):
    token = None
    with ProxySelenium(headless=True) as driver:
        driver.get(START_LOGIN_URL)
        driver.set_window_size(1920, 1080)

        _click(driver, 'span.button.button--primary.outline')
        _enter(driver, 'input[type=email]', user_name)
        _click(driver, '#anmelden')
        _enter(driver, 'input[type=password]', password)

        start = time.time()
        while token is None:
            token = _get_token_from_url(driver.current_url)
            if time.time() - start > WAIT_TIME:
                log('More than {} seconds elapsed... Cancelling'.format(str(WAIT_TIME)))
                break

    if token is None:
        raise ValueError('Token could not be found')
    log('Found token {}'.format(token))
    return token


def _click(driver, selector):
    input_element = WebDriverWait(driver, WAIT_TIME).until(
        expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    input_element.click()


def _enter(driver, selector, text):
    input_element = _get_element(driver, selector)
    input_element.send_keys(text)
    input_element.send_keys(Keys.ENTER)


def _get_element(driver, selector):
    input_element = WebDriverWait(driver, WAIT_TIME).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, selector)))
    return input_element


def _get_token_from_url(url):
    token_name = 'access_token'
    query_strings = urlparse.parse_qs(
        urlparse.urlparse(url).query, keep_blank_values=True)
    if token_name in query_strings:
        log('Found token in URL: {}'.format(url))
        token = query_strings[token_name][0]
        return token.replace(' ', '+')
    return None
