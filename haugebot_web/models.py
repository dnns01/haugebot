import os

from django.db import models

from haugebot_web import twitch_api
from .managers import TwitchUserManager


class Setting(models.Model):
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=50)


class TwitchColor(models.Model):
    twitch_name = models.CharField(max_length=20)
    display_name = models.CharField(max_length=20)
    color = models.CharField(max_length=7)


class WusstestDuSchon(models.Model):
    advertised_command = models.CharField(max_length=20)
    text = models.TextField(max_length=450)
    use_prefix = models.BooleanField(default=True, verbose_name="Präfix verwenden")
    active = models.BooleanField(default=True, verbose_name="Aktiv")


class TwitchUser(models.Model):
    objects = TwitchUserManager()

    id = models.BigIntegerField(primary_key=True)
    login = models.CharField(max_length=50)
    access_token = models.CharField(max_length=50)
    refresh_token = models.CharField(max_length=50)
    last_login = models.DateTimeField(null=True)
    admin = models.BooleanField(default=False)

    def update_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.save()

    @property
    def is_authenticated(self):
        broadcaster_id = int(os.getenv("BROADCASTER_ID"))
        if self.id == broadcaster_id or self.admin:
            return True
        try:
            broadcaster = TwitchUser.objects.get(pk=broadcaster_id)
            return twitch_api.is_mod(self, broadcaster)
        except TwitchUser.DoesNotExist:
            return False
