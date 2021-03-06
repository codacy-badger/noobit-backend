from server import settings
import logging
import time
from contextlib import suppress

import asyncio
import uvicorn
from uvicorn.loops.uvloop import uvloop_setup

from fastapi import Depends, FastAPI, APIRouter
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from server.startup.register_client import register_session
from server.startup.register_orm import register_tortoise

#! skip register kafka for use with aiokafka
# from kafka.register_kafka import register_kafka

# TODO      copy paste code from minigryph: at startup should initialize all exchange classes 
# TODO      from abstract factory and store them in settings file
# TODO      then we can load them into the views.account file 
# TODO      ==> rather just send all the minigryph data to a kafka topic instead of printing it, 
# TODO      ==> and have fastapi connect to that topic + the same database

#TODO       load httpx client at startup : https://www.python-httpx.org/advanced/

from server.views import cache, html, json, items, users, fastapi_users, charts


app = FastAPI()


origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app=app, 
    db_url="sqlite://fastapi.db", 
    modules={"models": ["models.orm_models"]}, 
    generate_schemas=True,
    )

register_session(
    app=app
    )

# register_kafka(
#     app=app,
#     config={"bootstrap.servers": "localhost:9092", "group.id": "cryptofeed"},
#     loop = asyncio.get_event_loop()
#     )

router = APIRouter()


# Test Routers
app.include_router(router, prefix="/tasks")
app.include_router(items.router)
app.include_router(charts.router, prefix="/charts", tags=["charts"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(fastapi_users.router, prefix="/users", tags=["users"])

# Routers we want to actually use in production
app.include_router(cache.account.router, prefix="/cache", tags=["cached_data"])
app.include_router(json.public.router, prefix="/json/public", tags=["public_data", "json"])
app.include_router(json.private.router, prefix="/json/private", tags=["private_data", "json"])
app.include_router(json.trade.router, prefix="/json/trade", tags=["private_trading", "json"])
app.include_router(html.public.router, prefix="/html/public", tags=["public_data", "html"])
app.include_router(html.private.router, prefix="/html/private", tags=["private_data", "html"])


# app.mount("/static", StaticFiles(directory="server/static"), name="static")
# we don't need static files anymore



# Tring to add a background task based on the following example :
# https://github.com/miguelgrinberg/python-socketio/issues/282

# We need to find a way to shutdown th bg task/infinite loop when uvicorn is shutdown

@app.on_event('startup')
async def signal_startup():
    settings.UVICORN_RUNNING = True


@app.on_event('shutdown')
async def signal_shutdown():
    settings.UVICORN_RUNNING = False


async def run_uvicorn():
    uvicorn.run(app, host='localhost', port=8000)


# def run_server():
#     from server import main_server
    
#     logging.info("Initiating application startup.")
#     main_server.run("main_app:app", host='localhost', port=8000, reload=False)
