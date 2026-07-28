import asyncio
import selectors
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from uvicorn.config import Config
from uvicorn.server import Server


async def main():
    config = Config("app.main:app", host="127.0.0.1", port=8000, loop="asyncio")
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(main())
