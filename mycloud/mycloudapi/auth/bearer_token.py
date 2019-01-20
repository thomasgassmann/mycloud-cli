import os
import time
import asyncio
import threading
import urllib.parse as urlparse
from multiprocessing import Process
from bs4 import BeautifulSoup
from mitmproxy import proxy, options, http
from mitmproxy.tools.dump import DumpMaster
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from mycloud.logger import log


CHROME = 'chromium'
CHROME_DRIVER = 'chromedriver'
WAIT_TIME = 15
JS_FILE = 'undetectable-headless-browser.js'
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 9090

START_LOGIN_URL = 'https://start.mycloud.ch'


def get_bearer_token(user_name: str, password: str):
    _run_proxy()

    driver = _get_web_driver()
    driver.get(START_LOGIN_URL)
    driver.set_window_size(1920, 1080)

    _click(driver, 'span.button.button--primary.outline')
    _enter(driver, 'input[type=email]', user_name)
    _click(driver, '#anmelden')
    _enter(driver, 'input[type=password]', password)

    token = None
    start = time.time()
    while token is None:
        token = _get_token_from_url(driver.current_url)
        if time.time() - start > WAIT_TIME:
            log('More than {} seconds elapsed... Cancelling'.format(str(WAIT_TIME)))
            break
    driver.quit()
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


def _run_proxy():
    def _wrapper():
        opts = options.Options(listen_host=PROXY_HOST, listen_port=PROXY_PORT)
        opts.add_option('body_size_limit', int, 0, '')
        opts.add_option('keep_host_header', bool, True, '')
        pconf = proxy.config.ProxyConfig(opts)

        dump_master = DumpMaster(None)
        dump_master.server = proxy.server.ProxyServer(pconf)
        dump_master.addons.add(_InjectScripts())
        dump_master.run()
        
    process = Process(target=_wrapper)
    process.start()


def _get_web_driver():
    user_agent = '''
        Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36
    '''

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    chrome_options.add_argument('--proxy-server=http://{0}:{1}'.format(PROXY_HOST, str(PROXY_PORT)))
    chrome_options.add_argument('user-agent={0}'.format(user_agent))
    driver = webdriver.Chrome(CHROME_DRIVER, chrome_options=chrome_options)

    return driver


class _InjectScripts:

    def __init__(self):
        current_directory = os.path.dirname(__file__)
        js_file = os.path.join(current_directory, JS_FILE)
        js_to_execute = open(js_file).read()
        self._js = js_to_execute

    def response(self, flow: http.HTTPFlow):
        ct_header = 'Content-Type'
        if (ct_header in flow.response.headers and \
                flow.response.headers[ct_header] != 'text/html') or \
                not flow.response.status_code == 200:
            return

        html = BeautifulSoup(flow.response.text, 'lxml')
        container = html.head or html.body
        if container:
            script = html.new_tag('script', type='text/javascript')
            script.string = self._js
            container.insert(0, script)
            flow.response.text = str(html)
