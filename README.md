# Earth Jukebox

Python 3.12+ va aiogram 3 yordamida yaratilgan asinxron Telegram bot.
`/start` menyuni ko'rsatadi. Har bir Earth-data bo'limi tanlangan lokatsiya uchun
ma'lumot, yillik grafik va shu qator asosida yaratilgan audio yuboradi.

## Features

`Temperature` and `Cloud Coverage` use NASA POWER daily point data. `Sea Level`
uses NOAA CO-OPS monthly means where a matching gauge is mapped. `Wildfires`
uses NASA EONET curated events. `Vegetation` uses mid-year MODIS NDVI composites
from ORNL DAAC, scaled by 100.

`Listen` turns each feature's yearly values into audio: temperature controls
pitch, sea level controls beat speed, cloud coverage controls note density and
duration, fire counts control rhythm and intensity, and vegetation selects the
instrument timbre.

`Time Machine` lets users choose a feature, location, and inclusive year range
from 2000 to 2026. When a live API is unavailable, interpolated illustrative
test data is clearly identified in the response.

## Persistence and Achievements

SQLite stores Telegram users, dataset/location selections, generated MP3 bytes,
and activity history in `data/earth_jukebox.sqlite3` by default. Override this
with `DATABASE_PATH` in `.env`. `/history` shows recent actions and `/achievements`
shows badge progress. Badges unlock automatically: First Sound (first audio),
Earth Explorer (3 locations), Data Scientist (5 data layers), Climate Listener
(audio from 3 climate layers), and Earth Composer (5 audio tracks).

## Data Sources

- Temperature and cloud coverage: NASA POWER daily point data.
- Wildfires: NASA EONET curated wildfire events, not every satellite fire detection.
- Sea level: NOAA CO-OPS monthly mean gauges. Global uses a San Francisco gauge proxy;
	Indian Ocean currently falls back to illustrative test data because no station is mapped.
- Vegetation: ORNL DAAC / NASA MODIS MOD13Q1 mid-year NDVI composite, scaled by 100.

These public endpoints require no extra API key. Requests use timeouts and cache
successful results briefly; on timeout, HTTP error, or unavailable location, the bot
uses the per-feature illustrative test data and labels the source in its response.

## O'rnatish

Python 3.12 yoki undan yangisini o'rnating. Loyiha papkasida virtual muhit yarating
va faollashtiring:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`.env.example` faylidan `.env` nusxa yarating va `BOT_TOKEN` qiymatiga Telegram
bot tokenini kiriting:

```powershell
Copy-Item .env.example .env
```

Botni ishga tushiring:

```powershell
python -m app.bot
```

Botga Telegram orqali `/start` yuboring.