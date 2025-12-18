import os

from django.db import models
from django.utils import timezone

from haugebot_web import twitch_api
from .managers import TwitchUserManager


class Setting(models.Model):
    wusstest_du_schon_prefix = models.CharField(max_length=50, verbose_name="Präfix")
    wusstest_du_schon_loop = models.PositiveIntegerField(verbose_name="Pause (in Minuten)")


class WusstestDuSchon(models.Model):
    command = models.CharField(max_length=20)
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
        return self.is_broadcaster or self.is_admin or self.is_mod

    @property
    def is_broadcaster(self):
        return self.id == int(os.getenv("BROADCASTER_ID"))

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_mod(self):
        try:
            broadcaster = TwitchUser.objects.get(pk=int(os.getenv("BROADCASTER_ID")))
            return twitch_api.is_mod(self, broadcaster)
        except TwitchUser.DoesNotExist:
            return False


class Whisper(models.Model):
    author = models.TextField(max_length=50)
    content = models.TextField(max_length=500)
    received_at = models.DateTimeField(default=timezone.now)


class Timer(models.Model):
    name = models.CharField(max_length=100)
    interval = models.PositiveIntegerField(default=30)
    next_time = models.DateTimeField(default=timezone.now)
    announce = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.next_time:
            self.next_time = self.next_time.replace(second=0, microsecond=0)
        # self.announce = False
        super().save(*args, **kwargs)


class TimerText(models.Model):
    timer = models.ForeignKey(Timer, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
