#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Toan Vo <thien@toan.pro>"

import datetime
import os
import redis
from dateutil import tz
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon import functions
from telethon.tl.types import PeerChannel, PeerUser
import telethon.sync
from telethon.sessions import StringSession
import schedule, time

load_dotenv()

local_tz = tz.gettz(os.getenv('TZ', 'Asia/Ho_Chi_Minh'))

# TELEGRAM CONFIG
# Get api_hash at https://my.telegram.org
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
RECEIVER_ID = int(os.getenv('RECEIVER_ID'))
STRING_SESSION = os.getenv('STRING_SESSION')

log = open('runtime.log', 'a+')

if not STRING_SESSION: 
    log.write("{}\tString session not found".format(datetime.datetime.now()))
    raise SystemExit()

# REDIS CONFIG
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PASS = os.getenv('REDIS_PASS')
REDIS_PORT = os.getenv('REDIS_PORT')

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, decode_responses=True)

# channel which got messages
channel = PeerChannel(channel_id=CHANNEL_ID)
receiver = PeerUser(RECEIVER_ID)

def job():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    client.start()

    client.get_dialogs()

    offset = r.get('offset')

    if offset:
        offset = int(offset)
    else:
        offset = 0
    messages = client(functions.messages.GetHistoryRequest(
        peer=channel,
        limit=2000,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=offset,
        add_offset=0,
        hash=0))

    messages.messages.reverse()
    for message in messages.messages:
        msg = '{0}\n\n{1}\n\n{2}\n'.format(str(message.date.astimezone(local_tz)), message.message, '*' * 10)
        client.send_message(receiver, msg)
        id = message.id
        if (id > offset):
            r.set('offset', id)
            r.set('last_push', str(datetime.datetime.now().astimezone(local_tz)))
            offset = id

    log.write("{} Done".format(str(datetime.datetime.now())))
    log.close()

schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)