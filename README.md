# Lunar Movie Client

A production-grade Telegram movie search bot built with Python 3.13, Pyrogram v2, MongoDB (Motor), TMDb API, and Internet Archive API.

---

## Features

- **Storage channel indexing** — drop video files into configured Telegram channels; the bot indexes them automatically.
- **Auto filename parsing** — detects title, year, quality, codec, and language from filenames.
- **TMDb integration** — rich movie cards with poster, cast, director, trailer link, genres, rating.
- **Internet Archive fallback** — searches for legally available public-domain / CC-licensed movies.
- **Full search** — text-index, regex, fuzzy, partial with pagination.
- **Inline mode** — `@BotUsername movie name` from any chat.
- **Request system** — users request missing movies; admins are notified and can fulfill.
- **Admin panel** — /stats, /broadcast, /ban, /unban, /addadmin, /removeadmin, /logs, /requests.
- **Premium features** — watchlist, favorites, search history, trending, genre browser, similar movies.
- **Rate limiting & flood protection** — per-user request throttle.
- **Auto-delete** — sent files are deleted after a configurable timeout.

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo>
cd lunar-movie-client
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Description |
|---|---|
| `API_ID` | Telegram API ID from my.telegram.org |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | Bot token from @BotFather |
| `BOT_USERNAME` | Bot username without @ |
| `MONGODB_URI` | MongoDB connection string |
| `TMDB_API_KEY` | TMDb API key (free at themoviedb.org) |
| `STORAGE_CHANNELS` | Comma-separated channel IDs (e.g. `-1001234567890`) |
| `ADMINS` | Comma-separated admin user IDs |
| `LOG_CHANNEL` | (Optional) Channel ID for bot logs |

### 2. Run with Docker Compose

```bash
docker compose up -d --build
```

Logs:

```bash
docker compose logs -f bot
```

### 3. Run locally (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```

---

## Storage Channel Setup

1. Create a private Telegram channel.
2. Add the bot as an admin with **Post Messages** permission.
3. Copy the channel ID (use `@userinfobot` or check Telegram Web; starts with `-100…`).
4. Add it to `STORAGE_CHANNELS` in `.env`.
5. Upload video files — the bot auto-indexes them.

---

## Bot Commands

### User

| Command | Description |
|---|---|
| `/start` | Main menu |
| `/movie <title>` | Search a movie |
| `/trending` | Trending movies this week |
| `/recent` | Recently indexed movies |
| `/watchlist` | Your watchlist |
| `/favorites` | Your favorites |
| `/history` | Your search history |
| `/request <title>` | Request a missing movie |
| `/myrequests` | View your requests |
| `/help` | Help message |

### Admin

| Command | Description |
|---|---|
| `/admin` | Admin panel |
| `/stats` | Bot statistics |
| `/broadcast` | Broadcast a message to all users |
| `/ban <id>` | Ban a user |
| `/unban <id>` | Unban a user |
| `/addadmin <id>` | Promote a user to admin |
| `/removeadmin <id>` | Remove an admin |
| `/requests` | View pending movie requests |
| `/logs` | View or download bot logs |

---

## Architecture

```
bot/
├── configs/         # Config loading from .env
├── database/
│   ├── client.py    # Motor connection + index creation
│   ├── models.py    # Pydantic models
│   └── repositories/
│       ├── movies.py
│       ├── users.py
│       └── requests.py
├── services/
│   ├── tmdb/        # TMDb API client
│   ├── archive/     # Internet Archive API client
│   └── search/      # Search engine (text + regex)
├── modules/
│   ├── file_parser.py  # Filename → title/year/quality/codec/lang
│   ├── movie_card.py   # Formatted movie card text
│   └── keyboards.py    # All InlineKeyboardMarkup builders
├── filters/         # Pyrogram custom filters (admin, banned)
├── helpers/         # Generic utilities
├── utils/
│   ├── logger.py    # Rotating file + console logger
│   └── decorators.py   # rate_limit, admin_required, log_errors
├── handlers/
│   ├── start.py     # /start, /help
│   ├── search.py    # /movie, /trending, /recent, etc.
│   ├── admin.py     # Admin commands + callback
│   ├── callbacks.py # All callback_query routing
│   ├── inline.py    # Inline query handler
│   ├── channel.py   # Storage channel indexer
│   └── request.py   # /request, /myrequests
└── main.py          # Entry point
```

---

## Legal Notice

- **TMDb** is used for movie metadata only (titles, posters, cast, trailers). No files are obtained from TMDb.
- **Internet Archive** links are provided only for public-domain or Creative Commons licensed content.
- **Telegram storage channels** are used exclusively for files uploaded by the bot owner / administrators.
- This bot does not facilitate the distribution of copyrighted content without authorization.
