#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging
import time
from signal import SIGINT, SIGTERM

import aiogram
import feedparser
from aiogram import types
from aiogram.types import ParseMode

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger()


class TelegramRssBot:
    fn_date_tuple = "date_tuple.txt"

    def __init__(self, bot_token: str, rss_url: str, receiver_id: str, interval: int):
        self.bot = aiogram.Bot(token=bot_token)
        self.dispatcher = aiogram.Dispatcher(bot=self.bot)
        self.dispatcher.register_message_handler(self.message_handler)
        self.rss_url = rss_url
        self.receiver_id = receiver_id
        self.interval = interval
        self.date_tuple = tuple(time.gmtime())
        self.read_date_tuple()

    def read_date_tuple(self):
        log.debug(f"read_date_tuple")
        try:
            with open(self.fn_date_tuple) as f:
                self.date_tuple = tuple([int(t) for t in f.read().strip().split()])
        except Exception as e:  # whatever
            log.debug(str(e))

    def write_date_tuple(self):
        log.debug(f"write_date_tuple")
        with open(self.fn_date_tuple, mode='w') as f:
            f.write(" ".join([str(t) for t in self.date_tuple]))

    async def message_handler(self, message: types.Message):
        msg = f"This bot is not interactive. It just sends items from {self.rss_url} to {self.receiver_id}."
        await message.answer(msg)

    async def fetch_rss(self):
        while True:
            log.debug(f"fetch_rss")
            feed = feedparser.parse(self.rss_url)
            entries = [e for e in feed.entries if e.published_parsed > self.date_tuple]
            if entries:
                for entry in reversed(entries):
                    log.info(entry.title)
                    log.info(entry.id)
                    msg = f'<a style="color:red" href="{entry.link}"><b>{entry.title}</b></a>\n{entry.description}'
                    await self.bot.send_message(self.receiver_id, msg, parse_mode=ParseMode.HTML,
                                                disable_web_page_preview=True)
                    self.date_tuple = entry.published_parsed
                    self.write_date_tuple()
            await asyncio.sleep(self.interval)

    async def run(self):
        try:
            poll_updates_task = asyncio.get_event_loop().create_task(self.dispatcher.start_polling())
            fetch_rss_task = asyncio.get_event_loop().create_task(self.fetch_rss())
            done, pending = await asyncio.wait({fetch_rss_task, poll_updates_task})
            for p in pending:
                p.cancel()
                await asyncio.shield(p)
        finally:
            await self.bot.close()


async def async_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bot_token', metavar='bot-token')
    parser.add_argument('rss_url', metavar='rss-url')
    parser.add_argument('receiver_id', metavar='receiver-id')
    parser.add_argument('-i', '--interval', default='60')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()
    log.debug(args)

    if args.verbose > 1:
        log.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        log.setLevel(logging.INFO)
    elif args.verbose == 0:
        log.setLevel(logging.WARNING)

    main_task = asyncio.ensure_future(TelegramRssBot(
        bot_token=args.bot_token,
        rss_url=args.rss_url,
        receiver_id=args.receiver_id,
        interval=int(args.interval)
    ).run())

    for signal in [SIGINT, SIGTERM]:
        asyncio.get_event_loop().add_signal_handler(signal, main_task.cancel)

    await main_task


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except asyncio.CancelledError:
        pass
