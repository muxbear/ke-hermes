import asyncio
import sys

if sys.platform == "win32":
    import uvicorn.loops.asyncio as _uvicorn_loops

    _uvicorn_loops.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.server:app",
        host="127.0.0.1",
        port=8000,
        reload=sys.platform != "win32",
    )
