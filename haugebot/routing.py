from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/wordcloud/$', consumers.WordCloudConsumer.as_asgi()),
]