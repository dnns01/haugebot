"""haugebot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from haugebot_web import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name="home"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('login/redirect/', views.login_redirect, name="login_redirect"),
    path('wusstest_du_schon/', views.wusstest_du_schon, name="wusstest_du_schon"),
    path('wusstest_du_schon/new/', views.wusstest_du_schon_new, name="wusstest_du_schon_new"),
    path('wusstest_du_schon/edit/<int:text_id>', views.wusstest_du_schon_edit, name="wusstest_du_schon_edit"),
    path('wusstest_du_schon/active', views.wusstest_du_schon_active, name="wusstest_du_schon_active"),
    path('wusstest_du_schon/remove', views.wusstest_du_schon_remove, name="wusstest_du_schon_remove"),
    path('whispers', views.whispers, name="whispers"),
    path('wordcloud/', views.wordcloud, name="wordcloud"),
    path('wordcloud/live/<str:id>', views.wordcloud_live, name="wordcloud_live")
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)