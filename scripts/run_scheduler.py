"""Start de scheduler standalone (zonder FastAPI)."""
import asyncio
import platform
import signal

if platform.system() == "Windows":
    import asyncio as _asyncio
    _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())

from app.logging_config import configure_logging
from app.scheduler.scheduler import start_scheduler, stop_scheduler


async def main() -> None:
    configure_logging()
    print("Scheduler gestart. Ctrl+C om te stoppen.")
    await start_scheduler()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass
    await stop_event.wait()
    await stop_scheduler()
    print("Scheduler gestopt.")


if __name__ == "__main__":
    asyncio.run(main())
