import os
import asyncio
import logging
from bs4 import BeautifulSoup
from mitmproxy import proxy, options, http
from mitmproxy.tools.dump import DumpMaster
from threading import Thread
from mitmproxy.tools.main import master
from selenium import webdriver


JS_FILE = 'undetectable-headless-browser.js'
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 49111
CHROME = 'chromium'
CHROME_DRIVER = 'chromedriver'


class ProxySelenium:

    def __init__(self, headless: bool):
        self._urls = []
        self._get_web_driver(headless)
        self._run_proxy()

    @property
    def urls(self):
        return self._urls

    def __enter__(self):
        return self._driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._driver.quit()

    def _run_proxy(self):
        logging.debug('Running selenium proxy...')

        def _wrapper(url_list):
            asyncio.set_event_loop(asyncio.new_event_loop())
            opts = options.Options(
                listen_host=PROXY_HOST, listen_port=PROXY_PORT)
            opts.add_option('body_size_limit', int, 0, '')
            pconf = proxy.config.ProxyConfig(opts)

            dump_master = DumpMaster(None)
            dump_master.server = proxy.server.ProxyServer(pconf)
            dump_master.addons.add(_InjectScripts(url_list))
            dump_master.run()

        t = Thread(target=_wrapper, daemon=True, args=(self._urls,))
        t.start()

        logging.debug('Started selenium proxy successfully...')

    def _get_web_driver(self, headless):
        user_agent = '''
            Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36
        '''

        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument('headless')
        proxy_str = '--proxy-server=http://{0}:{1}'.format(
            PROXY_HOST, str(PROXY_PORT))
        chrome_options.add_argument(proxy_str)
        chrome_options.add_argument('user-agent={0}'.format(user_agent))
        driver = webdriver.Chrome(CHROME_DRIVER, chrome_options=chrome_options)

        self._driver = driver


class _InjectScripts:

    def __init__(self, url_list):
        current_directory = os.path.dirname(__file__)
        js_file = os.path.join(current_directory, JS_FILE)
        js_to_execute = open(js_file).read()
        self._js = js_to_execute
        self._list = url_list

    def response(self, flow: http.HTTPFlow):
        self._list.append(flow.request.url)
        ct_header = 'Content-Type'
        if ct_header in flow.response.headers and \
                flow.response.headers[ct_header] == 'text/html' and \
                flow.response.status_code == 200:
            self.inject_scripts(flow)

    def inject_scripts(self, flow: http.HTTPFlow):
        html = BeautifulSoup(flow.response.text, 'lxml')
        container = html.head or html.body
        if container:
            script = html.new_tag('script', type='text/javascript')
            script.string = self._js
            container.insert(0, script)
            flow.response.text = str(html)
