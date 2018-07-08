import os, tempfile, zipfile, io
from sys import platform

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.abspath('..'))

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from logger import log
import time
from threading import Thread
import urllib.parse as urlparse
import urllib.request


if platform == 'win32':
    CHROME_DRIVER_URL = 'https://chromedriver.storage.googleapis.com/2.37/chromedriver_win32.zip'
    CHROME_DRIVER_NAME = 'chromedriver.exe'
else:
    CHROME_DRIVER_URL = 'https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip'
    CHROME_DRIVER_NAME = 'chromedriver'
CHROME_DIR = 'chrome'

START_LOGIN_URL = 'https://www.mycloud.ch/login?type=login&cid=myc_LP_login'


def get_bearer_token(user_name, password):
    driver = _get_web_driver()
    
    driver.get(START_LOGIN_URL)
    
    wait_time = 15
    
    input_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=email]')))
    input_element.send_keys(user_name)
    input_element.send_keys(Keys.ENTER)

    input_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, 'password')))
    input_element.send_keys(password)
    input_element.send_keys(Keys.ENTER)

    token = None
    start = time.time()
    while token is None:
        token = get_token_from_url(driver.current_url)
        if time.time() - start > wait_time:
            print(f'More than {str(wait_time)} seconds elapsed... Cancelling')
            break
    if token is None:
        raise ValueError('Token could not be found')
    driver.quit()
    log(f'Found token {token}')
    return token


def get_token_from_url(url):
    token_name = 'access_token'
    query_strings = urlparse.parse_qs(urlparse.urlparse(url).query, keep_blank_values=True)
    if token_name in query_strings:
        log(f'Found token in URL: {url}')
        token = query_strings[token_name][0]
        return token.replace(' ', '+')
    return None


def _get_web_driver():
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    chrome_options.add_argument('user-agent={0}'.format(user_agent))
    chrome_options.add_argument('proxy-server=localhost:8080')
    driver = webdriver.Chrome(_get_file(CHROME_DIR, CHROME_DRIVER_NAME, CHROME_DRIVER_URL), chrome_options=chrome_options)
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


if __name__ == '__main__':
    while True:
        try:
            token = get_bearer_token('thomas.gassmann@hotmail.com', '***REMOVED***')
            print(f'Got token {token}')
        except Exception as ex:
            print(ex)