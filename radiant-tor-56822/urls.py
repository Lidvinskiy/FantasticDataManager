"""DataManager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from DatawizManager import views as vs
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# from django.contrib import admin

urlpatterns = [
    url(r'^$', vs.Loginpage, name='home'),
    url(r'^login/$', vs.login, name='login'),
    url(r'^main/$', vs.main_page, name='main'),
    url(r'get_data/$', vs.get_base_data_to_html, name='get_data'),
    url(r'change_inform/$', vs.change_inform, name='change_inform'),
    url(r'ping_for_queue/$', vs.ping_for_queue, name='ping_for_queue'),
    url(r'^logout$', vs.logout, name='logout')
]
urlpatterns += staticfiles_urlpatterns()

