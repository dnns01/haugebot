import os
import json

import requests
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import Http404, JsonResponse, HttpResponse, HttpRequest

from .forms import BaseForm
from .models import WusstestDuSchon, Setting, Whisper


# Create your views here.
def home(request):
    return render(request, "home.html", {'title': 'HaugeBot'})


@login_required(login_url="/login")
def wordcloud(request):
    id = os.getenv("DJANGO_WORDCLOUD_LIVE_ID")
    host = os.getenv("DJANGO_ALLOWED_HOST1")
    embed_link = f"{request.scheme}://{host}{reverse('wordcloud_live', args=(id,))}" if request.user.is_broadcaster else ""
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


# <editor-fold desc="Wusstest du Schon">
@login_required(login_url="/login")
def wusstest_du_schon(request: HttpRequest) -> HttpResponse:
    settings_form = modelform_factory(Setting, form=BaseForm,
                                      fields=('wusstest_du_schon_prefix', 'wusstest_du_schon_loop'))
    loop_texts = WusstestDuSchon.objects.all()
    active = "config"

    if active_param := request.GET.get("active"):
        active = active_param

    if request.method == "POST":
        active = request.POST["form-active"]

        if active == "config":
            form = settings_form(request.POST, instance=Setting.objects.first())
            if form and form.is_valid():
                form.save()

    return render(request, "did_you_know/index.html", {'title': 'Wusstest du Schon?', 'active': active,
                                                       "config_form": settings_form(instance=Setting.objects.first()),
                                                       "loop_texts": loop_texts})


@login_required(login_url="/login")
def wusstest_du_schon_new(request: HttpRequest) -> HttpResponse:
    wusstest_du_schon_form = modelform_factory(WusstestDuSchon, form=BaseForm,
                                               fields=('command', 'text', 'use_prefix', 'active'))
    if request.method == "POST":
        form = wusstest_du_schon_form(request.POST)

        if form.is_valid():
            form.save()
            return redirect("/wusstest_du_schon?active=texts")

    form = wusstest_du_schon_form()

    return render(request, "did_you_know/edit.html", {'title': 'Wusstest du Schon?', "form": {"form": form}})


@login_required(login_url="/login")
def wusstest_du_schon_edit(request: HttpRequest, text_id: int) -> HttpResponse:
    text = get_object_or_404(WusstestDuSchon, pk=text_id)
    wusstest_du_schon_form = modelform_factory(WusstestDuSchon, form=BaseForm,
                                               fields=('command', 'text', 'use_prefix', 'active'))
    if request.method == "POST":
        form = wusstest_du_schon_form(request.POST, instance=text)

        if form.is_valid():
            form.save()
            return redirect("/wusstest_du_schon?active=texts")

    form = wusstest_du_schon_form(instance=text)

    return render(request, "did_you_know/edit.html", {'title': 'Wusstest du Schon?', "form": {"form": form}})


@login_required(login_url="/login")
def wusstest_du_schon_active(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            command = get_object_or_404(WusstestDuSchon, pk=payload["id"])
            field_name = payload["field"]
            if field_name == "prefix":
                command.use_prefix = payload["active"]
                field = command.use_prefix
            elif field_name == "active":
                command.active = payload["active"]
                field = command.active
            command.save()

            return JsonResponse({"active": field})
        except (json.decoder.JSONDecodeError, KeyError):
            pass

    raise Http404


@login_required(login_url="/login")
def wusstest_du_schon_remove(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            command = get_object_or_404(WusstestDuSchon, pk=payload["id"])
            command.delete()
        except (json.decoder.JSONDecodeError, KeyError):
            pass

        return JsonResponse({})

    raise Http404

# </editor-fold>

@login_required(login_url="/login")
def whispers(request):
    whisper_messages = Whisper.objects.all().order_by("-received_at")

    return render(request, "list_whispers.html", {'title': 'Geflüster', "whispers": whisper_messages})
