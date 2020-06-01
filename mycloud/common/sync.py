import asyncio


def run_sync(future):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(future)
