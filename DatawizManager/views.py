import os

from django.shortcuts import render
from django.http import HttpResponse
from dwapi import datawiz
import pandas as pd
import datetime
import BAL
import DatawizManager.forms as forms
import ast
import json


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


def get_base_data_to_html(request, shops='', date_from_first='', date_to_first='', date_from_second='',
                          date_to_second=''):
    date_from_f = datetime.datetime.strptime(request.GET['date_from_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_f = datetime.datetime.strptime(request.GET['date_to_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_from_s = datetime.datetime.strptime(request.GET['date_from_second'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_s = datetime.datetime.strptime(request.GET['date_to_second'].encode('utf-8'), '%m/%d/%Y').date()
    shops_int = ast.literal_eval(request.GET.getlist('shops')[0])
    query = BAL.create_base_inform(request.session['login'], request.session['key'], shops_int, date_from_f,
                                   date_to_f,
                                   date_from_s, date_to_s).base_information_table.to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive'], border=0)
    return HttpResponse(query)


def change_inform(request, shops='', date_from_first='', date_to_first='', date_from_second='',
                  date_to_second=''):
    date_from_f = datetime.datetime.strptime(request.GET['date_from_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_f = datetime.datetime.strptime(request.GET['date_to_first'].encode('utf-8'), '%m/%d/%Y').date()
    date_from_s = datetime.datetime.strptime(request.GET['date_from_second'].encode('utf-8'), '%m/%d/%Y').date()
    date_to_s = datetime.datetime.strptime(request.GET['date_to_second'].encode('utf-8'), '%m/%d/%Y').date()
    shops_int = ast.literal_eval(request.GET.getlist('shops')[0])
    query = BAL.create_change_inform(request.session['login'], request.session['key'], shops_int, date_from_f,
                                     date_to_f,
                                     date_from_s, date_to_s)
    data = {}
    data['first'] = query[0].to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive', 'table-report'], border=0)
    data['second'] = query[1].to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-responsive', 'table-report'], border=0)
    json_data = json.dumps(data)
    return HttpResponse(json_data)
