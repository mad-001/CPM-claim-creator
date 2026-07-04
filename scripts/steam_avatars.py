#!/usr/bin/env python3
"""Resolve Steam avatars for online players and write avatars.json for the map.
Stores { steamid64: {"url": <avatarfull>, "ts": <epoch last seen>} } and prunes
entries not seen within MAX_AGE_DAYS. Only URLs are stored (a few KB total)."""
import json, os, time, urllib.request

KEY = "2057C52BE9EE4962E3010F53A8248195"
PLAYERS_API = os.environ.get("CC_API", "http://192.168.1.27:26906") + "/api/getplayersonline"
OUT = os.environ.get("CC_OUT",
    "/mnt/server/gameservers/DoubleTap/7d2d/Mods/PrismaCore/ClaimCreator/avatars.json")
MAX_AGE_DAYS = 14

now = int(time.time())
cache = {}
if os.path.exists(OUT):
    try:
        cache = json.load(open(OUT))
    except Exception:
        cache = {}

# who is online right now (Steam players only have Steam avatars)
players = json.load(urllib.request.urlopen(PLAYERS_API, timeout=10))
ids = [p["steamid"].replace("Steam_", "") for p in players
       if str(p.get("steamid", "")).startswith("Steam_")]

# resolve in batches of 100
for i in range(0, len(ids), 100):
    batch = ",".join(ids[i:i + 100])
    url = ("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
           f"?key={KEY}&steamids={batch}")
    data = json.load(urllib.request.urlopen(url, timeout=15))
    for p in data.get("response", {}).get("players", []):
        cache[p["steamid"]] = {"url": p.get("avatarfull", ""), "ts": now}

# prune anything not seen within the age limit
cutoff = now - MAX_AGE_DAYS * 86400
cache = {k: v for k, v in cache.items()
         if isinstance(v, dict) and v.get("ts", 0) >= cutoff}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(cache, open(OUT, "w"))
print(f"avatars.json: {len(cache)} entries, {os.path.getsize(OUT)} bytes  (pruned older than {MAX_AGE_DAYS}d)")
