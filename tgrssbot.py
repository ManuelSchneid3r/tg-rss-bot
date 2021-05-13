#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging
import time
from signal import SIGINT, SIGTERM

import aiogram
import aiohttp
import feedparser
from aiogram import types
from aiogram.types import ParseMode


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
        self.old_ids = []

    def read_date_tuple(self):
        logging.debug(f"read_date_tuple")
        try:
            with open(self.fn_date_tuple) as f:
                self.date_tuple = tuple([int(t) for t in f.read().strip().split()])
        except Exception as e:  # whatever
            logging.debug(str(e))

    def write_date_tuple(self):
        logging.debug(f"write_date_tuple")
        with open(self.fn_date_tuple, mode='w') as f:
            f.write(" ".join([str(t) for t in self.date_tuple]))

    async def message_handler(self, message: types.Message):
        msg = f"This bot is not interactive. It just sends items from {self.rss_url} to {self.receiver_id}."
        await message.answer(msg)

    async def fetch_and_relay_rss(self):
        logging.debug(f"fetch_rss")
        async with aiohttp.request('GET', self.rss_url) as resp:
            feed = feedparser.parse(await resp.text())
            entries = [e for e in feed.entries if e.published_parsed > self.date_tuple and e.id not in self.old_ids]
            if entries:
                for entry in reversed(entries):
                    logging.info(f"{entry.published} {entry.id}")
                    msg = f'<a style="color:red" href="{entry.link}"><b>{entry.title}</b></a>\n{entry.description}'
                    await self.bot.send_message(self.receiver_id, msg, parse_mode=ParseMode.HTML,
                                                disable_web_page_preview=True)
                    self.date_tuple = entry.published_parsed
                    self.write_date_tuple()
            self.old_ids = [e.id for e in feed.entries]

    async def run(self):
        tg_task = asyncio.get_event_loop().create_task(self.dispatcher.start_polling())
        rss_task = asyncio.get_event_loop().create_task(self.fetch_and_relay_rss())
        try:
            while True:
                done, pending = await asyncio.wait({rss_task, tg_task}, timeout=self.interval,
                                                   return_when=asyncio.FIRST_EXCEPTION)
                if tg_task.done():
                    logging.warning(str(tg_task.exception()))
                    tg_task.cancel()
                    tg_task = asyncio.get_event_loop().create_task(self.dispatcher.start_polling())
                    await asyncio.sleep(self.interval)
                elif rss_task.done() and rss_task.exception():
                    logging.warning(str(rss_task.exception()))
                    await asyncio.sleep(self.interval)
                rss_task.cancel()
                rss_task = asyncio.get_event_loop().create_task(self.fetch_and_relay_rss())
        except asyncio.CancelledError:
            pass
        finally:
            tg_task.cancel()
            rss_task.cancel()
            await asyncio.shield(asyncio.wait({rss_task, tg_task}))
            await self.bot.close()


async def async_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bot_token', metavar='bot-token')
    parser.add_argument('rss_url', metavar='rss-url')
    parser.add_argument('receiver_id', metavar='receiver-id')
    parser.add_argument('-i', '--interval', default='60')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()

    if args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s - %(message)s')
    elif args.verbose == 1:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s - %(message)s')
    elif args.verbose == 0:
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s:%(levelname)s - %(message)s')

    logging.debug(args)

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
    asyncio.run(async_main())
