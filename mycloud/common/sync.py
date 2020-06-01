import asyncio


def run_sync(future):
    loop = asyncio.new_event_loop()
    task = loop.create_task(future)
    return loop.run_until_complete(task)
