import os

import requests
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, modelform_factory
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import BaseForm
from .models import WusstestDuSchon, Setting


# Create your views here.
def home(request):
    return render(request, "home.html", {'title': 'HaugeBot'})


@login_required(login_url="/login")
def wusstest_du_schon(request):
    wusstest_du_schon_form_set = modelformset_factory(WusstestDuSchon, form=BaseForm,
                                                  fields=('advertised_command', 'text', 'use_prefix', 'active'))
    settings_form = modelform_factory(Setting, form=BaseForm,
                                     fields=('wusstest_du_schon_prefix', 'wusstest_du_schon_loop'))
    active = "config"
    form = None

    if request.method == "POST":
        active = request.POST["form-active"]

        if active == "config":
            form = settings_form(request.POST, instance=Setting.objects.first())
        elif active == "wusstestdu":
            form = wusstest_du_schon_form_set(request.POST, request.FILES)

        if form and form.is_valid():
            form.save()

    forms = {"Konfiguration": {
        "display": "card",
        'type': 'form',
        'name': 'config',
        'form': settings_form(instance=Setting.objects.first()),
    },
        "Texte": {
            'display': 'card',
            'type': 'formset',
            'name': 'wusstestdu',
            'formset': wusstest_du_schon_form_set(),
            'remove_url': 'wusstest_du_schon_remove',
        },
    }

    return render(request, "form.html", {'title': 'Wusstest du Schon?', 'forms': forms, 'active': active})


@login_required(login_url="/login")
def wusstest_du_schon_remove(request, id):
    WusstestDuSchon.objects.filter(pk=id).delete()

    return redirect("/wusstest_du_schon")


#@login_required(login_url="/login")
def wordcloud(request):
    id = os.getenv("DJANGO_WORDCLOUD_LIVE_ID")
    embed_link = "" #f"{request.scheme}://{request.headers['Host']}{reverse('wordcloud_live', args=(id,))}" if request.user.is_broadcaster else ""
    return render(request, "wordcloud.html", {'title': 'Wordcloud', "ws_url": os.getenv("WORDCLOUD_WS_URL"),
                                              "session_key": request.session.session_key, "embed_link": embed_link})


def wordcloud_live(request, id):
    if id == os.getenv("DJANGO_WORDCLOUD_LIVE_ID"):
        return render(request, "live-wordcloud.html", {"ws_url": os.getenv("WORDCLOUD_WS_URL")})


def login(request):
    client_id = os.getenv("CLIENT_ID")
    redirect_uri = os.getenv("REDIRECT_URI")
    url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=moderation:read"
    return redirect(url)


def logout(request):
    django_logout(request)
    return redirect("/")


def login_redirect(request):
    code = request.GET.get('code')
    user = exchange_code(code)
    if user:
        twitch_user = authenticate(request, user=user)
        twitch_user = list(twitch_user).pop()
        django_login(request, twitch_user)

    return redirect("/")


def exchange_code(code):
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    redirect_uri = os.getenv("REDIRECT_URI")
    url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={redirect_uri}"
    response = requests.post(url)
    if response.status_code == 200:
        credentials = response.json()

        response = requests.get("https://api.twitch.tv/helix/users", headers={
            'Authorization': f'Bearer {credentials["access_token"]}',
            'Client-Id': client_id
        })

        user = response.json()["data"][0]

        return {'id': user['id'], 'login': user['login'], 'access_token': credentials['access_token'],
                'refresh_token': credentials['refresh_token']}

    return None
