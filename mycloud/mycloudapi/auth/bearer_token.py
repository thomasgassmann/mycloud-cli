import os
import tempfile
import zipfile
import io
from sys import platform

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.abspath('..'))

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from threading import Thread
import urllib.parse as urlparse
import urllib.request
from mycloud.logger import log


CHROME_DRIVER_URL = 'https://chromedriver.storage.googleapis.com/2.37/chromedriver_win32.zip'
CHROME_DRIVER_NAME = 'chromedriver.exe'
CHROME_DIR = 'chrome'

START_LOGIN_URL = 'https://www.mycloud.ch/login?type=login&cid=myc_LP_login'


def get_bearer_token(user_name: str, password: str):
    driver = _get_web_driver()

    driver.get(START_LOGIN_URL)

    wait_time = 15

    input_element = WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=email]')))
    input_element.send_keys(user_name)
    input_element.send_keys(Keys.ENTER)

    input_element = WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located((By.ID, 'password')))
    input_element.send_keys(password)
    input_element.send_keys(Keys.ENTER)

    token = None
    start = time.time()
    while token is None:
        token = get_token_from_url(driver.current_url)
        if time.time() - start > wait_time:
            log('More than {} seconds elapsed... Cancelling'.format(str(wait_time)))
            break
    driver.quit()
    if token is None:
        raise ValueError('Token could not be found')
    log('Found token {}'.format(token))
    return token


def get_token_from_url(url):
    token_name = 'access_token'
    query_strings = urlparse.parse_qs(
        urlparse.urlparse(url).query, keep_blank_values=True)
    if token_name in query_strings:
        log('Found token in URL: {}'.format(url))
        token = query_strings[token_name][0]
        return token.replace(' ', '+')
    return None


def _get_web_driver():
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    chrome_options.add_argument('user-agent={0}'.format(user_agent))
    if platform != 'win32':
        path = '/usr/lib/chromium-browser/chromedriver'
    else:
        chrome_options.add_argument('proxy-server=localhost:8080')
        path = _get_file(CHROME_DIR, CHROME_DRIVER_NAME, CHROME_DRIVER_URL)
    driver = webdriver.Chrome(path, chrome_options=chrome_options)
    return driver


def _get_file(dir_name, relative_path, url):
    dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), dir_name)
    if not os.path.isdir(dir):
        os.makedirs(dir)
    file_path = os.path.join(dir, relative_path)
    if os.path.isfile(file_path):
        return file_path
    response = urllib.request.urlopen(url)
    zip_ref = zipfile.ZipFile(io.BytesIO(response.read()))
    zip_ref.extractall(dir)
    zip_ref.close()
    return file_path
