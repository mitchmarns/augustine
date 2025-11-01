import requests, datetime, os

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
LAT, LON = 40.70, -77.60
CITY_NAME = "Augustine"
VERSION = "v2.4"  # bump when you redeploy

# ── Fetch current + today's high/low (Open-Meteo, no key) ──────────────────────
resp = requests.get(
    f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
    "precipitation,weather_code,wind_speed_10m"
    "&daily=temperature_2m_max,temperature_2m_min"
    "&forecast_days=1"
    "&timezone=auto",
    timeout=20
)
resp.raise_for_status()
data = resp.json()
w = data["current"]
d = data["daily"]

temp_c = float(w["temperature_2m"])
feels_c = float(w["apparent_temperature"])
hum = int(w["relative_humidity_2m"])
wind_mps = float(w["wind_speed_10m"])
wind_mph = wind_mps * 2.237
code = int(w["weather_code"])

hi_c = float(d["temperature_2m_max"][0])
lo_c = float(d["temperature_2m_min"][0])
hi_f = hi_c * 9/5 + 32
lo_f = lo_c * 9/5 + 32

# ── Weather code → emoji + label ───────────────────────────────────────────────
def sky_from_code(c: int):
    if c == 0: return "☀️", "clear sky"
    if c == 1: return "🌤️", "mostly clear"
    if c == 2: return "⛅", "partly cloudy"
    if c == 3: return "☁️", "overcast"
    if c in (45, 48): return "🌫️", "fog"
    if c in (51, 53, 55): return "🌦️", "drizzle"
    if c in (56, 57): return "🥶🌧️", "freezing drizzle"
    if c in (61, 63, 65): return "🌧️", "rain"
    if c in (66, 67): return "🥶🌧️", "freezing rain"
    if c in (71, 73, 75): return "🌨️", "snow"
    if c == 77: return "🌨️", "snow grains"
    if c in (80, 81, 82): return "🌦️", "rain showers"
    if c in (85, 86): return "🌨️", "snow showers"
    if c == 95: return "⛈️", "thunderstorm"
    if c in (96, 99): return "⛈️🧊", "thunderstorm w/ hail"
    return "🌤️", "conditions"

sky_emoji, sky_label = sky_from_code(code)

# ── Moon (approx.) ─────────────────────────────────────────────────────────────
today = datetime.date.today()
yy, mm, dd = today.year, today.month, today.day
r = yy % 100
r %= 19
if r > 9: r -= 19
r = ((r * 11) % 30) + mm + dd
if mm < 3: r += 2
phase_index = (r + 2 - yy // 100 + yy // 400) % 30
illum = round(phase_index / 29.53 * 100)
phase_buckets = [
    "🌑 New Moon", "🌒 Waxing Crescent", "🌓 First Quarter",
    "🌔 Waxing Gibbous", "🌕 Full Moon", "🌖 Waning Gibbous",
    "🌗 Last Quarter", "🌘 Waning Crescent"
]
moon_name = phase_buckets[int(phase_index / 3.7)]
lower = moon_name.lower()

# ── Werewolf notes (dynamic) ───────────────────────────────────────────────────
notes = []
if "waning crescent" in lower or "new moon" in lower or "waxing crescent" in lower:
    notes.append("Many wolves avoid going out after sundown between **Third Quarter → First Quarter** (around the new moon).")
if "full moon" in lower:
    notes.append("**Full moon tonight:** the shift is **unavoidable** and **painful**; born wolves handle it best.")
elif "waxing gibbous" in lower:
    notes.append("**Waxing gibbous:** most **ill-tempered**; moodiness and restlessness peak for wolves before the full moon.")
elif "waning gibbous" in lower:
    notes.append("**Waning gibbous:** Wolves most **physically & emotionally exhausted** after the full moon.")
elif "new moon" in lower:
    notes.append("**New moon:** calmest period for wolves. Only time new wolves can be created via an **alpha** bite; others leave a mark but don’t pass the curse.")
werewolf_note = "\n".join(notes) if notes else "Wolves feel the lunar pull; phases influence mood, stamina, and control."

# ── Build embed ────────────────────────────────────────────────────────────────
temp_f = temp_c * 9/5 + 32
feels_f = feels_c * 9/5 + 32

desc = (
    f"{sky_emoji} **{sky_label.title()}**\n"
    f"**{temp_c:.0f}°C / {temp_f:.0f}°F**, "
    f"feels {feels_c:.0f}°C / {feels_f:.0f}°F\n"
    f"🔺 High {hi_c:.0f}°C / {hi_f:.0f}°F · 🔻 Low {lo_c:.0f}°C / {lo_f:.0f}°F\n"
    f"💨 {wind_mph:.0f} mph · 💧{hum}% humidity"
)

embed = {
    "color": 0x2F3136,
    "description": (
        "> ⠀\n"
        ">  **{city} · Weather & Moon** \n"
        "> ⠀\n"
        ">  {emoji} **{label}**\n"
        ">  **{temp_c:.0f}°C / {temp_f:.0f}°F**, feels {feels_c:.0f}°C / {feels_f:.0f}°F\n"
        ">  🔺 {hi_c:.0f}°C / {hi_f:.0f}°F · 🔻 {lo_c:.0f}°C / {lo_f:.0f}°F\n"
        ">  💨 {wind_mph:.0f} mph · 💧{hum}% humidity\n"
        "> ⠀\n"
        ">  {moon_name} ({illum}% lit)\n"
        "> ⠀\n"
        ">  *{werewolf_note}*\n"
        "> ⠀"
    ).format(
        city=CITY_NAME,
        emoji=sky_emoji,
        label=sky_label.title(),
        temp_c=temp_c, temp_f=temp_c*9/5+32,
        feels_c=feels_c, feels_f=feels_c*9/5+32,
        hi_c=hi_c, hi_f=hi_c*9/5+32,
        lo_c=lo_c, lo_f=lo_c*9/5+32,
        wind_mph=wind_mph,
        hum=hum,
        moon_name=moon_name,
        illum=illum,
        werewolf_note=werewolf_note
    ),
    "footer": {"text": f"Sky Watch · {VERSION}"},
    "timestamp": datetime.datetime.utcnow().isoformat()
}


payload = {"username": "Sky Watch", "embeds": [embed]}
res = requests.post(WEBHOOK_URL, json=payload, timeout=20)
print("Status:", res.status_code, "| Version:", VERSION)
