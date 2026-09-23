
import os
import sys
import requests

# ============================================================
# CONFIG
# ============================================================

OSU_TOKEN_URL = "https://osu.ppy.sh/oauth/token"
OSU_API_URL = "https://osu.ppy.sh/api/v2"

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

OSU_CLIENT_ID = os.environ["OSU_CLIENT_ID"]
OSU_CLIENT_SECRET = os.environ["OSU_CLIENT_SECRET"]


# ============================================================
# OSU AUTHENTICATION
# ============================================================

def get_osu_token():
    response = requests.post(
        OSU_TOKEN_URL,
        json={
            "client_id": int(OSU_CLIENT_ID),
            "client_secret": OSU_CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "public"
        },
        timeout=30
    )

    if not response.ok:
        print("Erreur OAuth osu! :", response.status_code)
        print(response.text)
        sys.exit(1)

    return response.json()["access_token"]


# ============================================================
# OSU USER
# ============================================================

def get_osu_user(token, username):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    response = requests.get(
        f"{OSU_API_URL}/users/@{username}/osu",
        headers=headers,
        timeout=30
    )

    if response.status_code == 404:
        print(f"Joueur osu! introuvable : {username}")
        return None

    if not response.ok:
        print(
            f"Erreur récupération {username} : "
            f"{response.status_code}"
        )
        print(response.text)
        return None

    return response.json()


# ============================================================
# SUPABASE
# ============================================================

def update_supabase(osu_user):
    user_id = osu_user["id"]
    username = osu_user["username"]

    country = osu_user.get("country", {})
    statistics = osu_user.get("statistics", {})

    data = {
        "osu_id": user_id,
        "osu_username": username,
        "country_code": country.get("code"),
        "country_name": country.get("name"),
        "global_rank": statistics.get("global_rank"),
        "country_rank": statistics.get("country_rank"),
        "pp": statistics.get("pp"),
        "accuracy": statistics.get("hit_accuracy"),
        "play_count": statistics.get("play_count"),
        "play_time": statistics.get("play_time"),
        "total_score": statistics.get("total_score"),
        "ranked_score": statistics.get("ranked_score"),
        "total_hits": statistics.get("total_hits"),
        "maximum_combo": statistics.get("maximum_combo")
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/osu_players",
        headers=headers,
        json=data,
        timeout=30
    )

    if not response.ok:
        print("Erreur Supabase :", response.status_code)
        print(response.text)
        return False

    print(
        f"✓ {username} | "
        f"Global #{data['global_rank']} | "
        f"FR #{data['country_rank']} | "
        f"{data['pp']} PP"
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    # Joueurs à synchroniser
    # Tu peux aussi remplacer cette liste par une lecture
    # depuis une autre table Supabase.
    players = [
        "Spleen"
    ]

    print("========================================")
    print("       OSU! → SUPABASE SYNC")
    print("========================================")

    token = get_osu_token()

    success = 0

    for username in players:

        print(f"\nRecherche de {username}...")

        osu_user = get_osu_user(
            token,
            username
        )

        if osu_user is None:
            continue

        if update_supabase(osu_user):
            success += 1

    print("\n========================================")
    print(f"Synchronisation terminée : {success}/{len(players)}")
    print("========================================")


if __name__ == "__main__":
    main()

