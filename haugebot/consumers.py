import json
import os

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from wordcloud import WordCloud
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("WORDCLOUD_SECRET")
words = {}
permitted = []
uuid = None


def make_image(uuid, words, permitted):
    permitted_words = {word: qty for (word, qty) in words.items() if word in permitted}
    if len(permitted_words) > 0:
        wc = WordCloud(background_color="black", width=1920, height=1080, min_font_size=1, relative_scaling=1)
        wc.generate_from_frequencies(permitted_words)

        wc.to_file(f"media/{uuid}.png")


class WordCloudConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            "wordcloud",
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            "wordcloud",
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "word_update":
            self.word_update(data)
        elif message_type == "permit":
            self.permit(data)
        elif message_type == "deny":
            self.deny(data)

        async_to_sync(self.channel_layer.group_send)(
            "wordcloud",
            {
                "type": "broadcast",
                "data": data
            }
        )

    def verify_session_key(self):
        return self.scope["session"].session_key is not None

    def word_update(self, data):
        global uuid, words, permitted

        if data.get("secret") != secret:
            return

        if uuid != data.get("uuid"):
            uuid = data.get("uuid")
            words = {}
            permitted = []

        if words != data.get("words"):
            words = data.get("words")
            make_image(uuid, words, permitted)

    def permit(self, data):
        if not self.verify_session_key():
            return
        word = data.get("word")
        if word not in permitted:
            permitted.append(word)
            make_image(uuid, words, permitted)

    def deny(self, data):
        if not self.verify_session_key():
            return
        word = data.get("word")
        if word in permitted:
            permitted.remove(word)
            make_image(uuid, words, permitted)

    def broadcast(self, event):
        message = {
            "uuid": uuid,
            "words": words,
            "permitted": permitted
        }
        self.send(text_data=json.dumps(message))
