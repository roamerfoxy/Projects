from coroweb import get
from aiohttp import web, WSMsgType
import desk
import functools


async def call_back_func(str, ws):
    await ws.send_str(str)


@get("/")
async def index(request):
    # async with request.app["db_pool"].acquire() as conn:
    # users = await User.findAll(conn)
    return {"__template__": "index.html"}


@get("/ws")
async def get_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app["ws"] = ws
    request.app["call_back_func"] = functools.partial(call_back_func,ws=ws)

    await ws.send_str("Hello from webserver")

    data = await ws.receive()
    if data.type == WSMsgType.close:
        await ws.close()
        del request.app["ws"]


@get("/api/desk/stand")
async def desk_stand(request):
    ws = request.app["ws"]
    call_back_func = request.app["call_back_func"]
    await desk.stand(call_back_func)
    await ws.send_str("Connection closing...")
    await ws.close()
    del request.app["ws"]
    del request.app["call_back_func"]


@get("/api/desk/sit")
async def desk_sit(request):
    ws = request.app["ws"]
    call_back_func = request.app["call_back_func"]
    await desk.sit(call_back_func)
    await ws.send_str("Connection closing...")
    await ws.close()
    del request.app["ws"]
    del request.app["call_back_func"]
