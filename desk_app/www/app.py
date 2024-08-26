import logging
import os

import aiohttp_jinja2
from aiohttp import web
from jinja2 import FileSystemLoader

# import orm
from coroweb import add_routes
import config


@web.middleware
async def logger(request, handler):
    logging.info("request: %s %s", request.method, request.path)
    resp = await handler(request)
    return resp


@web.middleware
async def response(request, handler):
    logging.info("response middleware...")
    r = await handler(request)
    if isinstance(r, web.StreamResponse):
        return r
    if isinstance(r, bytes):
        resp = web.Response(body=r)
        resp.content_type = "application/octet-stream"
        return resp
    if isinstance(r, str):
        if r.startswith("redirect:"):
            return web.HTTPFound(r[9:])
        resp = web.Response(body=r.encode("utf-8"))
        resp.content_type = "text/html;charset=utf-8"
        return resp
    if isinstance(r, dict):
        template = r.get("__template__")
        resp = aiohttp_jinja2.render_template(template, request, r, encoding="utf-8")
        resp.content_type = "text/html;charset=utf-8"
        return resp

    resp = web.Response(body=str(r).encode("utf-8"))
    resp.content_type = "text/plain;charset=utf-8"
    return resp


async def init_app():
    app = web.Application(middlewares=[logger, response])

    app["config"] = config.load_config(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config", "config_default.json"
        )
    )

    add_routes(app, "handlers")

    aiohttp_jinja2.setup(
        app,
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        ),
    )

    # await orm.init_db(app)

    logging.info("app is initialised...")
    return app


def main():
    app = init_app()
    web.run_app(app, host="192.168.1.120")


if __name__ == "__main__":
    main()
