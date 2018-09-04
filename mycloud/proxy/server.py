import asyncio
from aiohttp import web, RequestInfo
from aiohttp.web import BaseRequest
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder
from mycloud.streamapi import (
    DefaultUpStream,
    DefaultDownStream,
    CloudStreamAccessor,
    UpStreamExecutor,
    DownStreamExecutor
)
from mycloud.filesystem import FileManager, BasicRemotePath, BasicStringVersion


class AsyncUpStream(DefaultUpStream):
    def __init__(self, async_stream):
        super().__init__(0)
        self._stream = async_stream
        self.loop = asyncio.get_event_loop()

    def read(self, length: int):
        return self.loop.run_until_complete(self._stream.read(length))

    def close(self):
        self.loop.close()


class ProxyServer:
    def __init__(self, request_executor: MyCloudRequestExecutor, mycloud_dir: str):
        self._request_executor = request_executor
        self._mycloud_dir = mycloud_dir

    async def get(self, request):
        path = self._get_effective_path(request.rel_url)
        return web.Response(text=path)

    async def post(self, request: BaseRequest):
        path = self._get_effective_path(request.rel_url)

        upstream = AsyncUpStream(request.content)
        manager = FileManager(self._request_executor, [], None)
        manager.write_file(upstream, BasicRemotePath(path),
                           BasicStringVersion('v1.0'))
        return web.Response(text=path)

    def _get_effective_path(self, rel_url):
        return ObjectResourceBuilder.combine_cloud_path(self._mycloud_dir, str(rel_url))

    # TODO: add web socket
    # async def wshandle(request):
    #     ws = web.WebSocketResponse()
    #     await ws.prepare(request)

    #     async for msg in ws:
    #         if msg.type == web.WSMsgType.text:
    #             await ws.send_str("Hello, {}".format(msg.data))
    #         elif msg.type == web.WSMsgType.binary:
    #             await ws.send_bytes(msg.data)
    #         elif msg.type == web.WSMsgType.close:
    #             break

    #     return ws


def run_server(request_executor: MyCloudRequestExecutor, mycloud_dir: str, port: int):
    app = web.Application()
    handler = ProxyServer(request_executor, mycloud_dir)
    app.add_routes([web.get('/{tail:.*}', handler.get),
                    web.post('/{tail:.*}', handler.post)])

    web.run_app(app, port=port)
