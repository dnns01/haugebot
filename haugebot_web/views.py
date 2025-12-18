import datetime
import json
import os

import requests
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory, DateTimeInput, modelformset_factory
from django.http import Http404, JsonResponse, HttpResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .forms import BaseForm
from .models import WusstestDuSchon, Setting, Whisper, Timer, TimerText


# Create your views here.
def home(request):
    return render(request, "home.html", {'title': 'HaugeBot'})


# @login_required(login_url="/login")
# def wordcloud(request):
#     id = os.getenv("DJANGO_WORDCLOUD_LIVE_ID")
#     host = os.getenv("DJANGO_ALLOWED_HOST2")
#     embed_link = f"{request.scheme}://{host}{reverse('wordcloud_live', args=(id,))}" if request.user.is_broadcaster else ""
#     return render(request, "wordcloud.html", {'title': 'Wordcloud', "ws_url": os.getenv("WORDCLOUD_WS_URL"),
#                                               "session_key": request.session.session_key, "embed_link": embed_link})
#
#
# def wordcloud_live(request, id):
#     if id == os.getenv("DJANGO_WORDCLOUD_LIVE_ID"):
#         return render(request, "live-wordcloud.html", {"ws_url": os.getenv("WORDCLOUD_WS_URL")})


def login(request):
    client_id = os.getenv("DJANGO_CLIENT_ID")
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
    client_id = os.getenv("DJANGO_CLIENT_ID")
    client_secret = os.getenv("DJANGO_CLIENT_SECRET")
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
            command.active = payload["active"]
            command.save()

            return JsonResponse({"active": command.active})
        except (json.decoder.JSONDecodeError, KeyError):
            pass

    raise Http404


@login_required(login_url="/login")
def wusstest_du_schon_prefix(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            command = get_object_or_404(WusstestDuSchon, pk=payload["id"])
            command.use_prefix = payload["active"]
            command.save()

            return JsonResponse({"active": command.use_prefix})
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


# <editor-fold desc="Timer">
@login_required(login_url="/login")
def timer(request: HttpRequest) -> HttpResponse:
    timers = Timer.objects.all()

    return render(request, "timer/index.html", {'title': 'Timer', 'timers': timers})


@login_required(login_url="/login")
def timer_new(request: HttpRequest) -> HttpResponse:
    timer_form = modelform_factory(Timer, form=BaseForm,
                                   fields=('name', 'interval', 'next_time', 'announce', 'active'),
                                   widgets={'next_time': DateTimeInput(attrs={'type': 'datetime-local'}), }
                                   )
    timer_formset = modelformset_factory(TimerText, form=BaseForm, fields=('text',))
    if request.method == "POST":
        form = timer_form(request.POST)
        formset = timer_formset(request.POST)

        if form.is_valid() and formset.is_valid():
            timer = form.save()
            timer_texts = formset.save(commit=False)

            for text in timer_texts:
                text.timer = timer
                text.save()
            return redirect("timer_edit", timer_id=timer.id)

    form = timer_form()
    formset = timer_formset(queryset=TimerText.objects.none())

    return render(request, "timer/edit.html", {'title': 'Timer', "form": {"form": form, 'formset': formset}})


@login_required(login_url="/login")
def timer_edit(request: HttpRequest, timer_id: int) -> HttpResponse:
    timer = get_object_or_404(Timer, pk=timer_id)
    timer_form = modelform_factory(Timer, form=BaseForm,
                                   fields=('name', 'interval', 'next_time', 'announce', 'active'),
                                   widgets={'next_time': DateTimeInput(attrs={'type': 'datetime-local'}), }
                                   )
    timer_formset = modelformset_factory(TimerText, form=BaseForm, fields=('text',))

    if request.method == "POST":
        form = timer_form(request.POST, instance=timer)
        formset = timer_formset(request.POST, queryset=timer.timertext_set.all())

        if form.is_valid() and formset.is_valid():
            timer = form.save()
            timer_texts = formset.save(commit=False)

            for text in timer_texts:
                text.timer = timer
                text.save()
            return redirect("timer_edit", timer_id=timer_id)

    form = timer_form(instance=timer)
    formset = timer_formset(queryset=timer.timertext_set.all())

    return render(request, "timer/edit.html", {'title': 'Timer', "form": {"form": form, 'formset': formset}})


@login_required(login_url="/login")
def timer_active(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            timer = get_object_or_404(Timer, pk=payload["id"])
            timer.active = payload["active"]
            timer.save()

            return JsonResponse({"active": timer.active})
        except (json.decoder.JSONDecodeError, KeyError):
            pass

    raise Http404


@login_required(login_url="/login")
def timer_announce(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            command = get_object_or_404(Timer, pk=payload["id"])
            command.announce = payload["active"]
            command.save()

            return JsonResponse({"active": command.announce})
        except (json.decoder.JSONDecodeError, KeyError):
            pass

    raise Http404


@login_required(login_url="/login")
def timer_remove(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            command = get_object_or_404(Timer, pk=payload["id"])
            command.delete()
        except (json.decoder.JSONDecodeError, KeyError):
            pass

        return JsonResponse({})

    raise Http404


def api_timers_get(request: HttpRequest) -> JsonResponse:
    if request.method == "GET" and request.headers.get("secret") == os.getenv("DJANGO_API_SECRET"):
        timers = []
        for timer in Timer.objects.all():
            texts = [text.text for text in timer.timertext_set.all()]
            timers.append({
                "id": timer.id,
                "name": timer.name,
                "interval": timer.interval,
                "next_time": timer.next_time,
                "announce": timer.announce,
                "active": timer.active,
                "texts": texts
            })

        return JsonResponse({"timers": timers})

    return JsonResponse(
        {"detail": "Authentication required"},
        status=401
    )


@csrf_exempt
def api_timers_update(request: HttpRequest, timer_id: int) -> JsonResponse:
    if request.method == "POST" and request.headers.get("secret") == os.getenv("DJANGO_API_SECRET"):
        timer = get_object_or_404(Timer, pk=timer_id)

        try:
            data = json.loads(request.body)
            timer.next_time = datetime.datetime.fromisoformat(data["next_time"])
            timer.save()
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        texts = [text.text for text in timer.timertext_set.all()]
        return JsonResponse(
            {
                "id": timer.id,
                "name": timer.name,
                "interval": timer.interval,
                "next_time": timer.next_time,
                "announce": timer.announce,
                "active": timer.active,
                "texts": texts
            })

    return JsonResponse(
        {"detail": "Authentication required"},
        status=401
    )


# </editor-fold>

@login_required(login_url="/login")
def whispers(request):
    whisper_messages = Whisper.objects.all().order_by("-received_at")

    return render(request, "list_whispers.html", {'title': 'Geflüster', "whispers": whisper_messages})
