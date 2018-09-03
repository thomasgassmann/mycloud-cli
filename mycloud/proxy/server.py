from aiohttp import web, RequestInfo


async def get(request):
    path = request.rel_url
    return web.Response(text='')


async def post(request):
    path = request.rel_url
    return web.Response(text='')

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


def run_server():
    app = web.Application()
    app.add_routes([web.get('/{tail:.*}', get),
                    web.post('/{tail:.*}', post)])

    web.run_app(app)


if __name__ == '__main__':
    run_server()
