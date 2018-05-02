from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from browsermobproxy import Server
from time import sleep
from logger import log
import urllib.parse as urlparse
import urllib.request
import os, tempfile, zipfile, io


CHROME_DRIVER_URL = 'https://chromedriver.storage.googleapis.com/2.37/chromedriver_win32.zip'
CHROME_DIR = 'chrome'
CHROME_DRIVER_NAME = 'chromedriver.exe'

BROWSERMOB_URL = 'https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-2.1.4/browsermob-proxy-2.1.4-bin.zip'
BROWSERMOB_DIR = 'browsermob'
BROWSERMOB_RELATIVE_PATH = 'browsermob-proxy-2.1.4\\bin\\browsermob-proxy'

START_LOGIN_URL = 'https://start.mycloud.ch/'


def get_bearer_token():
    (proxy, server) = __get_proxy()
    driver = __get_web_driver(proxy)
    log('Please log in...')
    driver.get(START_LOGIN_URL)
    proxy.new_har()
    token = None
    while token is None:
        sleep(1)
        token = __get_token_if_available(proxy)
    server.stop()
    driver.quit()
    log(f'Found token {token}')
    return token


def __get_token_if_available(proxy):
    try:
        all_requests = [entry['request']['url'] for entry in proxy.har['log']['entries']]
        matching_requests = [s for s in all_requests if 'mycloud.ch/login' in s]
        log('Searching for token...')
        for matching_request in matching_requests:
            parsed = urlparse.urlparse(matching_request)
            parsed_access_token = urlparse.parse_qs(parsed.query)
            if 'access_token' in parsed_access_token:
                acccess_tokens = parsed_access_token['access_token']
                return acccess_tokens[0]
        return None
    except:
        return None


def __get_proxy():
    server = Server(__get_file(BROWSERMOB_DIR, BROWSERMOB_RELATIVE_PATH, BROWSERMOB_URL))
    server.start()
    proxy = server.create_proxy()
    return (proxy, server)


def __get_web_driver(proxy):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server={0}'.format(proxy.proxy))
    driver = webdriver.Chrome(__get_file(CHROME_DIR, CHROME_DRIVER_NAME, CHROME_DRIVER_URL), chrome_options=chrome_options)
    return driver


def __get_file(dir_name, relative_path, url):
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