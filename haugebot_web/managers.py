from django.contrib.auth import models


class TwitchUserManager(models.UserManager):
    def create_new_twitch_user(self, user):
        new_user = self.create(
            id=user['id'],
            login=user['login'],
            access_token=user['access_token'],
            refresh_token=user['refresh_token']
        )
        return new_user
