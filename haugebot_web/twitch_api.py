import os
from datetime import datetime

import requests
from django.utils.http import urlencode

token_url = "https://id.twitch.tv/oauth2/token?client_id={0}&client_secret={1}&grant_type=client_credentials"
clips_url = "https://api.twitch.tv/helix/clips?broadcaster_id={0}&first=100"
broadcaster_id = os.getenv("BROADCASTER_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
access_token = None


def get_access_token():
    global access_token

    response = requests.post(token_url.format(client_id, client_secret))
    credentials = response.json()
    access_token = credentials["access_token"]


def call(url):
    if access_token:
        response = requests.get(url, headers={
            'Authorization': 'Bearer {}'.format(access_token),
            'Client-Id': client_id
        })
        if response.status_code == 200:
            return response.json()
        else:
            get_access_token()
            response = requests.get(url, headers={
                'Authorization': 'Bearer {}'.format(access_token),
                'Client-Id': client_id
            })
            if response.status_code == 200:
                return response.json()
    else:
        get_access_token()
        response = requests.get(url, headers={
            'Authorization': 'Bearer {}'.format(access_token),
            'Client-Id': client_id
        })
        if response.status_code == 200:
            return response.json()


def get_clips(cursor=None, all_clips=False, today=False):
    clips = []
    url = clips_url.format(broadcaster_id)
    if cursor:
        url += "&after=" + cursor
    if today:
        url += "&started_at=" + get_date()

    clips_json = call(url)

    if data := clips_json.get("data"):
        for clip in data:
            if thumbnail_url := clip.get("thumbnail_url"):
                clip_url = thumbnail_url.split("-preview-")[0] + ".mp4"
                clips.append(clip_url)

    if all_clips:
        if pagination := clips_json.get("pagination"):
            if new_cursor := pagination.get("cursor"):
                clips.extend(get_clips(cursor=new_cursor, all_clips=all_clips, today=today))
    return clips


def get_date():
    now = datetime.now()
    dt = datetime(day=now.day, month=now.month, year=now.year)
    return dt.isoformat() + "Z"


def is_mod(user, broadcaster):
    response = requests.get(
        f"https://api.twitch.tv/helix/moderation/moderators?broadcaster_id={broadcaster.id}&user_id={user.id}",
        headers={
            'Authorization': f'Bearer {broadcaster.access_token}',
            'Client-Id': client_id
        })

    if response.status_code == 401 and response.json().get("message") == "Invalid OAuth token":
        if not refresh_access_token(broadcaster):
            return False
        return is_mod(user, broadcaster)

    return response.json().get("data") is not None


def refresh_access_token(broadcaster):
    url = "https://id.twitch.tv/oauth2/token?" + urlencode(
        {"grant_type": "refresh_token", "refresh_token": broadcaster.refresh_token, "client_id": client_id,
         "client_secret": client_secret})
    response = requests.post(url)

    if response.status_code == 400 and response.json().get("message") == "Invalid refresh token":
        return None

    json = response.json()
    access_token = json["access_token"]
    refresh_token = json["refresh_token"]
    broadcaster.update_tokens(access_token, refresh_token)
