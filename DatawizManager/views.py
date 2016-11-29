# coding=utf-8
import os
from _pylibmc import MemcachedError

from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache
from dwapi import datawiz
from rq import Queue, get_current_job
from worker import conn
import pandas as pd
import datetime
import BAL
import DatawizManager.forms as forms
import ast
import json
from django.conf import settings

q = Queue(connection=conn)

# повертае сторінку авторизації
def Loginpage(request):
    form_class = forms.LoginForm
    return render(request, 'Loginform.html', {'form': form_class})

# функція деавторизації
def logout(request):
    for key in request.session.keys():
        del request.session[key]
    form_class = forms.LoginForm
    return render(request, 'Loginform.html', {'form': form_class})

# повертае головну сторінку
def main_page(request):
    try:
        tr = request.session['key']
        return render(request, 'main.html')
    except KeyError:
        form_class = forms.LoginForm
        return render(request, 'Loginform.html', {'form': form_class})

# функція авторизації
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

# повертає базову інформацію по магазинам за проміжок часу в форматі json
def BAL_create_base_inform(getinform):
    try:
        query = BAL.create_base_inform(getinform.login, getinform.key, getinform.shops, getinform.date_from_f,
                                       getinform.date_to_f,
                                       getinform.date_from_s, getinform.date_to_s).base_information_table.to_html(
            classes=['table', 'table-striped', 'table-hover', 'table-responsive'], border=0)
    except:
        data = {}
        data['base'] = '<h3>Відсутні дані за вашим запитом</h3>'
        data['data'] = 'full'
        return json.dumps(data)
    data = {}
    data['base'] = query
    data['data'] = 'full'
    return json.dumps(data)

# перевіряе чи робота виконана ,якщо так то повертае результат
def ping_for_queue(request, shops='', date_from_first='', date_to_first='', date_from_second='',
                   date_to_second='', type=''):
    date_from_f = datetime.datetime.strptime(request.GET['date_from_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_f = datetime.datetime.strptime(request.GET['date_to_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_from_s = datetime.datetime.strptime(request.GET['date_from_second'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_s = datetime.datetime.strptime(request.GET['date_to_second'].encode('utf-8'), '%m/%d/%Y').date()
    shops_int = ast.literal_eval(request.GET.getlist('shops')[0])
    key = str(request.GET['type'].encode('utf-8')) + str(date_from_f) + str(date_to_f) + \
          str(date_from_s) + str(date_to_s) \
          + str(shops_int) + str(request.session['login'])
    if str(request.GET['type'].encode('utf-8')) == 'get_data':
        job = q.fetch_job(request.session['get_base_q_id'])
    elif str(request.GET['type'].encode('utf-8')) == 'change_inform':
        job = q.fetch_job(request.session['get_change_q_id'])
    if not job.is_finished:
        data = {}
        data['data'] = ''
        return HttpResponse(json.dumps(data))
    else:
        cache.set(key, job.result)
        return HttpResponse(job.result)

# запускає процес отримання базової інформації по магазинам , або повертае її з кеша
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
    if cache.get(key) is None:
        job = q.enqueue(
            BAL_create_base_inform, QueueBase(request.session['login'], request.session['key'], shops_int, date_from_f,
                                              date_to_f,
                                              date_from_s, date_to_s, key))
        request.session['get_base_q_id'] = job.id
        data = {}
        data['data'] = ''
        return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(cache.get(key))

# повертає інформацію про зміну продажу товарів в форматі json
def BAL_create_change_inform(getinform):
    try:
        query = BAL.create_change_inform(getinform.login, getinform.key, getinform.shops, getinform.date_from_f,
                                         getinform.date_to_f,
                                         getinform.date_from_s, getinform.date_to_s)
    except:
        data = {}
        data['first'] = '<h3>Відсутні дані за вашим запитом</h3>'
        data['second'] = '<h3>Відсутні дані за вашим запитом</h3>'
        data['data'] = 'full'
        return json.dumps(data)
    data = {}
    data['first'] = query[0].to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive', 'table-report'], border=0)
    data['second'] = query[1].to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive', 'table-report'], border=0)
    data['data'] = 'full'
    return json.dumps(data)

# запускає процес отримання інформації про зміну продажу товарів або повертає її з кешу
def change_inform(request, shops='', date_from_first='', date_to_first='', date_from_second='',
                  date_to_second='', type=''):
    date_from_f = datetime.datetime.strptime(request.GET['date_from_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_f = datetime.datetime.strptime(request.GET['date_to_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_from_s = datetime.datetime.strptime(request.GET['date_from_second'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_s = datetime.datetime.strptime(request.GET['date_to_second'].encode('utf-8'), '%m/%d/%Y').date()
    shops_int = ast.literal_eval(request.GET.getlist('shops')[0])
    key = str(request.GET['type'].encode('utf-8')) + str(date_from_f) + str(date_to_f) + \
          str(date_from_s) + str(date_to_s) \
          + str(shops_int) + str(request.session['login'])
    if cache.get(key) is None:
        job = q.enqueue(
            BAL_create_change_inform,
            QueueBase(request.session['login'], request.session['key'], shops_int, date_from_f,
                      date_to_f,
                      date_from_s, date_to_s, key))
        request.session['get_change_q_id'] = job.id
        data = {}
        data['data'] = ''
        return HttpResponse(json.dumps(data))

    else:
        return HttpResponse(cache.get(key))
