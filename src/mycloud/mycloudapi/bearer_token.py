import os, tempfile, zipfile, io

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.abspath('..'))

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from logger import log
from threading import Thread
import urllib.parse as urlparse
import urllib.request


CHROME_DRIVER_URL = 'https://chromedriver.storage.googleapis.com/2.37/chromedriver_win32.zip'
CHROME_DIR = 'chrome'
CHROME_DRIVER_NAME = 'chromedriver.exe'

START_LOGIN_URL = 'https://www.mycloud.ch/login?type=login&cid=myc_LP_login'


def get_bearer_token(user_name, password):
    driver = __get_web_driver()
    log('Please log in...')
    
    driver.get(START_LOGIN_URL)
    
    wait_time = 15
    
    input_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=email]')))
    input_element.send_keys(user_name)
    input_element.send_keys(Keys.ENTER)

    input_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, 'password')))
    input_element.send_keys(password)
    input_element.send_keys(Keys.ENTER)

    token = None
    while token is None:
        token = get_token_from_list(driver.current_url)
    driver.quit()
    log(f'Found token {token}')
    return token


def get_token_from_list(list):
    token_name = 'access_token'
    for item in list:
        query_strings = urlparse.parse_qs(urlparse.urlparse(item).query)
        if token_name in query_strings:
            return query_strings[token_name][0]
    return None


def __get_web_driver():
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    chrome_options.add_argument('user-agent={0}'.format(user_agent))
    chrome_options.add_argument('proxy-server=localhost:8080')
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