
import json
import os
import sys
from datetime import datetime, timezone

import requests


# ==========================================
# CONFIG
# ==========================================

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

JSON_FILE = "aredl-clan.json"


# ==========================================
# SUPABASE
# ==========================================

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}


def supabase_upsert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30,
    )

    if not response.ok:
        print(f"\nSupabase error on {table}:")
        print(response.status_code)
        print(response.text)

        response.raise_for_status()

    return response


def supabase_delete(table, params):
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    response = requests.delete(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    if not response.ok:
        print(f"\nSupabase delete error on {table}:")
        print(response.status_code)
        print(response.text)

        response.raise_for_status()

    return response


# ==========================================
# HELPERS
# ==========================================

def clean_name(name):
    if not name:
        return None

    return name.strip()


def parse_date(value):
    if not value:
        return None

    return value


def now():
    return datetime.now(timezone.utc).isoformat()


# ==========================================
# LOAD JSON
# ==========================================

print("Loading AREDL data...")

try:
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

except FileNotFoundError:
    print(f"ERROR: {JSON_FILE} not found.")
    sys.exit(1)

except json.JSONDecodeError as error:
    print("ERROR: Invalid JSON.")
    print(error)
    sys.exit(1)


# ==========================================
# CLAN
# ==========================================

clan = data.get("clan", {})
rank = data.get("rank", {})
records = data.get("records", [])

clan_id = clan.get("id")

if not clan_id:
    print("ERROR: Clan ID missing.")
    sys.exit(1)


print()
print("Clan:")
print(f"  Name: {clan.get('global_name')}")
print(f"  Tag:  {clan.get('tag')}")
print(f"  ID:   {clan_id}")

print()
print("AREDl Rank:")
print(f"  Rank:          {rank.get('rank')}")
print(f"  Extremes:      {rank.get('extremes')}")
print(f"  Extremes rank: {rank.get('extremes_rank')}")
print(f"  Hardest rank:  {rank.get('hardest_rank')}")
print(f"  Level points:  {rank.get('level_points')}")


# ==========================================
# UPSERT CLAN
# ==========================================

clan_data = {
    "id": clan_id,

    "name": clan.get("global_name") or clan.get("tag") or "Unknown",
    "tag": clan.get("tag"),
    "description": clan.get("description"),

    "aredl_rank": rank.get("rank"),
    "extremes_rank": rank.get("extremes_rank"),
    "hardest_rank": rank.get("hardest_rank"),
    "level_points": rank.get("level_points"),
    "extremes": rank.get("extremes"),

    "created_at": clan.get("created_at"),
    "updated_at": clan.get("updated_at"),

    "synced_at": now(),
}

supabase_upsert("clans", clan_data)

print("\nClan synchronized.")


# ==========================================
# BUILD MEMBERS
# ==========================================

members = {}

for record in records:

    player = record.get("submitted_by")

    if not player:
        continue

    player_id = player.get("id")

    if not player_id:
        continue

    if player_id not in members:

        members[player_id] = {
            "id": player_id,
            "clan_id": clan_id,

            "username": clean_name(
                player.get("username")
            ),

            "global_name": clean_name(
                player.get("global_name")
            ),

            "country": player.get("country"),

            "discord_id": player.get("discord_id"),

            "discord_avatar": player.get(
                "discord_avatar"
            ),

            "discord_avatar_decoration": player.get(
                "discord_avatar_decoration"
            ),

            "featured_badge_code": player.get(
                "featured_badge_code"
            ),

            "total_points": 0,
            "records_count": 0,

            "hardest_level": None,
            "hardest_level_id": None,
            "hardest_position": None,
            "hardest_points": None,

            "synced_at": now(),
        }


# ==========================================
# CALCULATE MEMBER STATS
# ==========================================

for record in records:

    player = record.get("submitted_by")
    level = record.get("level")

    if not player or not level:
        continue

    player_id = player.get("id")

    if player_id not in members:
        continue

    member = members[player_id]

    points = level.get("points") or 0
    position = level.get("position")

    member["total_points"] += points
    member["records_count"] += 1

    # Hardest = smallest AREDL position
    if position is not None:

        current_position = member["hardest_position"]

        if (
            current_position is None
            or position < current_position
        ):
            member["hardest_level"] = clean_name(
                level.get("name")
            )

            member["hardest_level_id"] = level.get(
                "level_id"
            )

            member["hardest_position"] = position

            member["hardest_points"] = points


# ==========================================
# SYNC MEMBERS
# ==========================================

print()
print(f"Members detected: {len(members)}")

for member in members.values():

    print(
        f"  {member['username']}: "
        f"{member['total_points']} points / "
        f"{member['records_count']} records"
    )

    supabase_upsert(
        "clan_members",
        member
    )


# ==========================================
# SYNC RECORDS
# ==========================================

print()
print(f"Records detected: {len(records)}")

for record in records:

    player = record.get("submitted_by")
    level = record.get("level")

    if not player or not level:
        continue

    member_id = player.get("id")

    if not member_id:
        continue

    record_data = {

        "id": record.get("id"),

        "clan_id": clan_id,

        "member_id": member_id,

        "submission_id": record.get(
            "submission_id"
        ),

        "level_id": level.get("id"),

        "gd_level_id": level.get(
            "level_id"
        ),

        "level_name": clean_name(
            level.get("name")
        ),

        "position": level.get(
            "position"
        ),

        "points": level.get(
            "points"
        ),

        "level_status": level.get(
            "status"
        ),

        "two_player": level.get(
            "two_player",
            False
        ),

        "requires_raw_footage": level.get(
            "requires_raw_footage",
            False
        ),

        "video_url": record.get(
            "video_url"
        ),

        "hide_video": record.get(
            "hide_video",
            False
        ),

        "is_verification": record.get(
            "is_verification",
            False
        ),

        "mobile": record.get(
            "mobile",
            False
        ),

        "achieved_at": parse_date(
            record.get("achieved_at")
        ),

        "completion_count": record.get(
            "completion_count",
            1
        ),

        "created_at": parse_date(
            record.get("created_at")
        ),

        "updated_at": parse_date(
            record.get("updated_at")
        ),

        "synced_at": now(),
    }

    supabase_upsert(
        "clan_records",
        record_data
    )


# ==========================================
# REMOVE OLD RECORDS
# ==========================================

# IDs currently present in AREDL
current_record_ids = {
    record.get("id")
    for record in records
    if record.get("id")
}

# We intentionally don't delete old records here.
# This prevents accidental data loss if AREDL
# temporarily returns an incomplete response.


# ==========================================
# DONE
# ==========================================

print()
print("===================================")
print("AREDl synchronization completed!")
print("===================================")
