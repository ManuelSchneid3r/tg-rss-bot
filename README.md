# Telegram RSS Bot

Minimal Telegram RSS Bot. Fetches RSS Feeds and sends them to Telegram. Based on `aiogram` and `feedparser`. ~100MB Docker image.

`docker`
```bash
docker build -t rss-bot "https://github.com/ManuelSchneid3r/tg-rss-bot.git#master"
docker run -d --name rss-bot --restart unless-stopped rss-bot "<BOT-TOKEN>" "<RSS-URL>" "<DESTINATOIN-ID>"
```

`docker-compose`
```yaml
version: '3.3'
services:
  tg-rss-bot:
    build: https://github.com/ManuelSchneid3r/tg-rss-bot.git
    image: tg-rss-bot
    container_name: tg-rss-bot
    restart: unless-stopped
    command: ["<BOT-TOKEN>", "<RSS-URL>", "<DESTINATOIN-ID>"]
```

Visit [@botfather](https://telegram.me/botfather) to get a bot token. The destination id can be a numeric Telegram identifier as well as the public @identifiers.