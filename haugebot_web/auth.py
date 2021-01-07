from django.contrib.auth.backends import BaseBackend

from .models import TwitchUser


class TwitchAuthenticationBackend(BaseBackend):
    def authenticated(self, request, user) -> TwitchUser:
        find_user = TwitchUser.objects.filter(id=user['id'])
        if len(find_user) == 0:
            TwitchUser.objects.create_new_twitch_user(user)
            return self.authenticate(request, user)
        return find_user

    def get_user(self, user_id):
        try:
            return TwitchUser.objects.get(pk=user_id)
        except TwitchUser.DoesNotExist:
            return None
