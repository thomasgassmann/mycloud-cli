import time
import asyncio
import logging
import urllib.parse as urlparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from mycloud.mycloudapi.auth.selenium_proxy import ProxySelenium


WAIT_TIME = 15
START_LOGIN_URL = 'https://www.mycloud.ch/login/'


async def open_for_cert():
    # TODO: problem with proxy only occurs when running async
    # removing async and "async_click" will fix proxy.
    with ProxySelenium(headless=False) as driver:
        await asyncio.sleep(2)
        driver.get('http://mitm.it')
        while any(driver.window_handles):
            pass


async def get_bearer_token(user_name: str, password: str, headless: bool):
    token = None
    proxy_selenium = ProxySelenium(headless=headless)
    with proxy_selenium as driver:
        await asyncio.sleep(2)
        driver.set_window_size(1920, 1080)
        driver.get(START_LOGIN_URL)

        _enter(driver, 'input#username', user_name)
        _enter(driver, 'input[type=password]', password)

        start = time.time()
        while token is None:
            token = _get_token_from_urls(proxy_selenium.urls)
            if time.time() - start > WAIT_TIME:
                break

    if token is None:
        raise ValueError('Token could not be found')
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


def _get_token_from_urls(urls):
    for url in urls:
        token_name = 'access_token'
        logging.debug(f'Looking for token in URL {url}...')
        query_strings = urlparse.parse_qs(
            urlparse.urlparse(url).query, keep_blank_values=True)
        if token_name in query_strings:
            token = query_strings[token_name][0]
            return token.replace(' ', '+')
    return None
