#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import json
import yaml
import toml
import random
from airtable import airtable 
from datetime import datetime

import asyncpg
import pytz
import uvicorn
from fastapi import Depends, FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

import data_api.lib_misc as lm
from data_api.models import (
    SubmitModel,
    ReadModel,
    UpdateModel
)


# ################################################### SETUP AND ARGUMENT PARSING
# ##############################################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())
dir_path = os.path.dirname(os.path.realpath(__file__))

config = {
    'postgresql': {
        'dsn': os.getenv('PG_DSN', 'postgres://user:pass@localhost:5432/db'),
        'min_size': 4,
        'max_size': 20
    },
    'proxy_prefix': os.getenv('PROXY_PREFIX', ''),
    'server': {
        'host': os.getenv('HOST', '127.0.0.1'),
        'port': int(os.getenv('PORT', '5000')),
        'log_level': os.getenv('LOG_LEVEL', 'info'),
        'timeout_keep_alive': 0,
    },
    'log_level': 'info',
    'airtable': {
        'base_id': os.getenv('AIRTABLE_BASE', ''),
        'api_key': os.getenv('AIRTABLE_API', ''),
    },
    'salt': os.getenv('SALT', 'OpenJusticePirates'),
}

VERSION = 1
START_TIME = datetime.now(pytz.utc)


async def get_db():
    global DB_POOL  # pylint:disable=global-statement
    conn = await DB_POOL.acquire()
    try:
        yield conn
    finally:
        await DB_POOL.release(conn)


def doc_hash(ecli):
    nonce = random.randint(1, 80000)
    return str(abs(hash(F"{ecli}{nonce}{config['salt']}")))

# ############################################################### SERVER ROUTES
# #############################################################################

app = FastAPI(root_path=config['proxy_prefix'])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ############################################################### SERVER ROUTES
# #############################################################################
@app.on_event("startup")
async def startup_event():
    global DB_POOL  # pylint:disable=global-statement
    if os.getenv('NO_ASYNCPG', 'false') == 'false':
        DB_POOL = await asyncpg.create_pool(**config['postgresql'])


@app.get("/")
def root():
    return lm.status_get(START_TIME, VERSION)


@app.post("/create")
async def create(query: SubmitModel, request: Request, db=Depends(get_db)):
    """
    Submit document endpoint
    """
    logger.info('Testing user key %s', query.user_key)
    # FIXME : Fix airtable key checking
    # at = airtable.Airtable(config['airtable']['base_id'], config['airtable']['api_key'])
    # data = at.get('Test Users')
    # at.get('Test Users', filter_by_formula=f"Key={query.user_key}")
    if query.user_key != 'test_key':
        raise HTTPException(status_code=401, detail="bad user key")

    ecli = f"ECLI:{query.country}:{query.court}:{query.year}:{query.identifier}"
    docHash = doc_hash(ecli)

    sql = """
    INSERT INTO ecli_document (
        ecli,
        country,
        court,
        year,
        identifier,
        text,
        meta,
        ukey,
        hash
    ) VALUES ( $1, $2, $3, $4, $5, $6, $7, $8, $9);
    """

    await db.execute(
        sql,
        ecli,
        query.country,
        query.court,
        query.year,
        query.identifier,
        query.text,
        query.meta,
        query.user_key,
        docHash,
    )
    logger.debug('Wrote ecli %s to database', ecli)
    return {'result': "ok", 'hash': docHash}


@app.get("/read")
def read(query: ReadModel, request: Request, db=Depends(get_db)):
    """
    Access document endpoint
    """
    return "ok"


@app.get("/update")
def update(query: UpdateModel, request: Request, db=Depends(get_db)):
    """
    Update document endpoint
    """
    return "ok"


@app.get("/hash/{dochash}", response_class=HTMLResponse)
async def gohash(dochash, db=Depends(get_db)):
    sql = """
    SELECT ecli, text FROM ecli_document WHERE hash = $1
    """

    res = await db.fetchrow(sql, dochash)
    return """
    <!DOCTYPE html>
    <html lang="en"><body style="font-family:verdana">
        <head><title>{ecli}</title></head>
        <body>
            {text}
        </body>
    </html>
    """.format(ecli=res['ecli'], text=res['text'])


@app.get("/html/{ecli}", response_class=HTMLResponse)
async def ecli(ecli, db=Depends(get_db)):
    sql = """
    SELECT ecli, text FROM ecli_document WHERE ecli = $1
    """

    res = await db.fetchrow(sql, ecli)
    return """
    <!DOCTYPE html>
    <html lang="en"><body style="font-family:verdana">
        <head><title>{ecli}</title></head>
        <body>
            {text}
        </body>
    </html>
    """.format(ecli=res['ecli'], text=res['text'])


# ##################################################################### STARTUP
# #############################################################################
def main():
    global config

    parser = argparse.ArgumentParser(description='Matching server process')
    parser.add_argument('--config', dest='config', help='config file', default=None)
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Debug mode')
    args = parser.parse_args()

    # XXX: Lambda is a hack : toml expects a callable
    if args.config:
        t_config = toml.load(['config_default.toml', args.config])
    else:
        t_config = toml.load('config_default.toml')

    config = {**config, **t_config}

    if args.debug:
        logger.setLevel(logging.getLevelName('DEBUG'))
        logger.debug('Debug activated')
        config['log_level'] = 'debug'
        config['server']['log_level'] = 'debug'
        logger.debug('Arguments: %s', args)
        logger.debug('config: %s', yaml.dump(config, indent=2))
        # logger.debug('config: %s', toml.dumps(config))

    uvicorn.run(
        app,
        **config['server']
    )


if __name__ == "__main__":
    main()
