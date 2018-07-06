import os
from bs4 import BeautifulSoup
from mitmproxy import ctx
from mitmproxy import http


dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, 'undetectable-headless-browser.js')) as f:
    js_content = f.read()


def response(flow: http.HTTPFlow):
    if flow.response.headers['Content-Type'] != 'text/html' or not flow.response.status_code == 200:
        return
    html = BeautifulSoup(flow.response.text, 'lxml')
    ctx.log.info(flow.id)
    container = html.head or html.body
    if container:
        script = html.new_tag('script', type='text/javascript')
        script.string = js_content
        container.insert(0, script)
        flow.response.text = str(html)