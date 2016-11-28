import os
from _pylibmc import MemcachedError

from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache
from dwapi import datawiz
from rq import Queue
from worker import get_conn
import pandas as pd
import datetime
import BAL
import DatawizManager.forms as forms
import ast
import json
conn = get_conn()


def Loginpage(request):
    form_class = forms.LoginForm
    return render(request, 'Loginform.html', {'form': form_class})


def logout(request):
    for key in request.session.keys():
        del request.session[key]
    form_class = forms.LoginForm
    return render(request, 'Loginform.html', {'form': form_class})


def main_page(request):
    try:
        tr = request.session['key']
        return render(request, 'main.html')
    except KeyError:
        form_class = forms.LoginForm
        return render(request, 'Loginform.html', {'form': form_class})


def login(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        key = request.POST.get('key')
        try:
            User = BAL.Creator.get_user_entity(login, key)
        except:
            form_class = forms.LoginForm
            return render(request, 'Loginform.html', {'form': form_class})
        request.session['login'] = login
        request.session['key'] = key
        request.session['user_name'] = User.name
        request.session['date_from'] = datetime.datetime.strftime(User.date_from.date(), '%m/%d/%Y')
        request.session['date_to'] = datetime.datetime.strftime(User.date_to.date(), '%m/%d/%Y')
        request.session['shops'] = list(zip(User.shops['Name'].tolist(), map(int, User.shops['ID'].tolist())))
        request.session['all_shops'] = map(int, User.shops['ID'].tolist())
        return render(request, 'main.html')
    form_class = forms.LoginForm
    return render(request, 'Loginform.html', {'form': form_class})


class QueueBase(object):
    def __init__(self, login, key, shops, date_from_f, date_to_f, date_from_s, date_to_s, key_to_cache):
        self.login = login
        self.key = key
        self.shops = shops
        self.date_from_f = date_from_f
        self.date_to_f = date_to_f
        self.date_from_s = date_from_s
        self.date_to_s = date_to_s
        self.key_to_cache = key_to_cache


def BAL_create_base_inform(getinform):
    query = BAL.create_base_inform(getinform.login, getinform.key, getinform.shops, getinform.date_from_f,
                                   getinform.date_to_f,
                                   getinform.date_from_s, getinform.date_to_s).base_information_table.to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive'], border=0)
    cache.set(getinform.key_to_cache, query)


def ping_for_queue(request, shops='', date_from_first='', date_to_first='', date_from_second='',
                  date_to_second=''):
    date_from_f = datetime.datetime.strptime(request.GET['date_from_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_f = datetime.datetime.strptime(request.GET['date_to_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_from_s = datetime.datetime.strptime(request.GET['date_from_second'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_s = datetime.datetime.strptime(request.GET['date_to_second'].encode('utf-8'), '%m/%d/%Y').date()
    shops_int = ast.literal_eval(request.GET.getlist('shops')[0])
    key = str(request.GET['type'].encode('utf-8')) + str(date_from_f) + str(date_to_f) + \
          str(date_from_s) + str(date_to_s) \
          + str(shops_int) + str(request.session['login'])
    if cache.get(key) is None:
        return HttpResponse('')
    else:
        return HttpResponse(cache.get(key))


def get_base_data_to_html(request, shops='', date_from_first='', date_to_first='', date_from_second='',
                          date_to_second=''):
    date_from_f = datetime.datetime.strptime(request.GET['date_from_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_f = datetime.datetime.strptime(request.GET['date_to_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_from_s = datetime.datetime.strptime(request.GET['date_from_second'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_s = datetime.datetime.strptime(request.GET['date_to_second'].encode('utf-8'), '%m/%d/%Y').date()
    shops_int = ast.literal_eval(request.GET.getlist('shops')[0])
    key = str(request.GET['type'].encode('utf-8')) + str(date_from_f) + str(date_to_f) + \
          str(date_from_s) + str(date_to_s) \
          + str(shops_int) + str(request.session['login'])
    print conn
    if cache.get(key) is None:
        q = Queue(connection=conn)
        q.enqueue(
            BAL_create_base_inform,QueueBase(request.session['login'], request.session['key'], shops_int, date_from_f,
                                             date_to_f,
                                             date_from_s, date_to_s, key))
        return HttpResponse('')
    else:
        return HttpResponse(cache.get(key))


def BAL_create_change_inform(getinform):
    query = BAL.create_change_inform(getinform.login, getinform.key, getinform.shops, getinform.date_from_f,
                                   getinform.date_to_f,
                                   getinform.date_from_s, getinform.date_to_s)
    data = {}
    data['first'] = query[0].to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive', 'table-report'], border=0)
    data['second'] = query[1].to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive', 'table-report'], border=0)
    json_data = json.dumps(data)

    cache.set(getinform.key_to_cache, json_data)


def change_inform(request, shops='', date_from_first='', date_to_first='', date_from_second='',
                  date_to_second=''):
    date_from_f = datetime.datetime.strptime(request.GET['date_from_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_f = datetime.datetime.strptime(request.GET['date_to_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_from_s = datetime.datetime.strptime(request.GET['date_from_second'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_s = datetime.datetime.strptime(request.GET['date_to_second'].encode('utf-8'), '%m/%d/%Y').date()
    shops_int = ast.literal_eval(request.GET.getlist('shops')[0])
    key = str(request.GET['type'].encode('utf-8')) + str(date_from_f) + str(date_to_f) + \
          str(date_from_s) + str(date_to_s) \
          + str(shops_int) + str(request.session['login'])
    if cache.get(key) is None:
        q = Queue(connection=conn)
        q.enqueue(
            BAL_create_change_inform,QueueBase(request.session['login'], request.session['key'], shops_int, date_from_f,
                                             date_to_f,
                                             date_from_s, date_to_s, key))
        return HttpResponse('')

    else:
        return HttpResponse(cache.get(key))
