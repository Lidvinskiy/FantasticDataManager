# coding=utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import datetime
from dwapi import datawiz
import pandas as pd


class UserEntity(object):
    def __init__(self, name, date_from, date_to, shops):
        self.name = name
        self.date_from = date_from
        self.date_to = date_to
        self.shops = shops

    def __repr__(self):
        return 'Name = %s, date_from = %s, date_to = %s\n Shops:\n %s' % (self.name, self.date_from, self.date_to,
                                                                          self.shops)


class DateInformation(object):
    def __init__(self, date_from, date_to, turnover, qty, receipt_qty, avr_receipt):
        self.date_from = date_from
        self.date_to = date_to
        self.turnover = turnover
        self.receipt_qty = receipt_qty
        self.qty = qty
        self.avr_receipt = avr_receipt

    def __repr__(self):
        return 'Date_from: %s , Date_to: %s, Turnover: %s, receipt_gty: %s, qty: %s, avr_receipt: %s' % (
            self.date_from, self.date_to, self.turnover,
            self.receipt_qty, self.qty,
            self.avr_receipt)


# конструктор класу створюе таблицю з двох таблиць (про продажі в магазинах за проміжок часу таблицю) та їх порівняння
class BaseInformation(object):
    def __init__(self, first_day, second_day):
        if first_day.date_from == first_day.date_to and second_day.date_from == second_day.date_to:
            first_day_date = str(first_day.date_from)
            second_day_date = str(second_day.date_from)
        else:
            first_day_date = '(' + str(first_day.date_from) + ',' + str(first_day.date_to) + ')'
            second_day_date = '(' + str(second_day.date_from) + ',' + str(second_day.date_to) + ')'
        data = {first_day_date: [first_day.turnover, first_day.receipt_qty, first_day.qty, first_day.avr_receipt],
                second_day_date: [second_day.turnover, second_day.receipt_qty, second_day.qty, second_day.avr_receipt]}
        table = pd.DataFrame(data, index=['Оборот', 'Кількість товарів', 'Кількість чеків', 'Середній чек'])
        table['Різниця'] = (table[first_day_date] - table[second_day_date]).round(2)
        table['Різниця в % '] = (
            table['Різниця'] / ((table[first_day_date] + table[second_day_date]) // 2) * 100).round(2)
        self.base_information_table = table

    def __repr__(self):
        return self.base_information_table.to_string().encode('utf-8')


class Creator(object):
    # повертає інормацію про кліента
    @staticmethod
    def get_user_entity(login, key):
        dw = datawiz.DW(login, key)
        client_info = dw.get_client_info()
        return UserEntity(client_info['name'].encode('utf-8'), client_info['date_from'], client_info['date_to'],
                          pd.DataFrame(client_info['shops'].items(), columns=['ID', 'Name']))

    # повертає інфомацію про продажі в магазинах за проміжок часу таблицю
    @staticmethod
    def get_period_information(login, key, user_shops, date_from, date_to):
        dw = datawiz.DW(login, key)
        turnover = dw.get_products_sale(products=['sum'], by='turnover',
                                        shops=user_shops,
                                        date_from=date_from,
                                        date_to=date_to)
        qty = dw.get_products_sale(products=['sum'], by='qty',
                                   shops=user_shops,
                                   date_from=date_from,
                                   date_to=date_to)
        receipt_qty = dw.get_products_sale(products=['sum'], by='receipts_qty',
                                           shops=user_shops,
                                           date_from=date_from,
                                           date_to=date_to)
        avr_receipt = (turnover['sum'].sum() / receipt_qty['sum'].sum()).round(2)
        return DateInformation(date_from, date_to, turnover['sum'].sum().round(2),
                               qty['sum'].sum().round(2),
                               receipt_qty['sum'].sum().round(2),
                               avr_receipt)

    # функція яка створюе дві таблиці про зміну продажу товарів
    @staticmethod
    def get_change_information(login, key,
                               user_shops, date_from_first,
                               date_to_first, date_from_second, date_to_second):
        dw = datawiz.DW(login, key)
        table_grow = pd.DataFrame(columns=('Зміна кількості продаж', 'Зміна обороту'))
        table_fall = pd.DataFrame(columns=('Зміна кількості продаж', 'Зміна обороту'
                                                                     ''))
        qty_first = dw.get_products_sale(products=['sum'], by='qty',
                                         shops=user_shops,
                                         date_from=date_from_first,
                                         date_to=date_to_first)
        turnover_first = dw.get_products_sale(products=['sum'], by='turnover',
                                              shops=user_shops,
                                              date_from=date_from_first,
                                              date_to=date_to_first)
        qty_second = dw.get_products_sale(products=['sum'], by='qty',
                                          shops=user_shops,
                                          date_from=date_from_second,
                                          date_to=date_to_second)
        turnover_second = dw.get_products_sale(products=['sum'], by='turnover',
                                               shops=user_shops,
                                               date_from=date_from_second,
                                               date_to=date_to_second)
        for product in qty_first:
            try:
                check_change = qty_first[product].sum() - qty_second[product].sum()
                if check_change == 0:
                    continue
                elif check_change > 0:
                    table_grow.loc[product] = (qty_first[product].sum() - qty_second[product].sum()).round(2), \
                                              (turnover_first[product].sum() - turnover_second[product].sum()).round(2)
                elif check_change < 0:
                    table_fall.loc[product] = (qty_first[product].sum() - qty_second[product].sum()).round(2), \
                                              (turnover_first[product].sum() - turnover_second[product].sum()).round(2)
            except KeyError:
                try:
                    check_change_gty = qty_first[product].sum()
                    table_grow.loc[product] = (check_change_gty.round(2),
                                               turnover_first[product].sum().round(2))
                    continue
                except KeyError:
                    try:
                        check_change_gty = qty_second[product].sum()
                        table_fall.loc[product] = (-1 * check_change_gty.round(2),
                                                   -1 * turnover_second[product].sum().round(2))
                        continue
                    except KeyError as error:
                        print error
                        continue
        return [table_grow.sort_values(['Зміна кількості продаж', 'Зміна обороту'], ascending=False),
                table_fall.sort_values(['Зміна кількості продаж', 'Зміна обороту'], ascending=True)]


#
def create_base_inform(login, key, shops, first_date_from, first_date_to, second_date_from, second_date_to):
    return BaseInformation(Creator.get_period_information(login, key, shops, first_date_from, first_date_to),
                           Creator.get_period_information(login, key, shops, second_date_from, second_date_to))


#
def create_change_inform(login, key, user_shops, first_date_from, first_date_to, second_date_from, second_date_to):
    return Creator.get_change_information(login, key, user_shops, first_date_from, first_date_to, second_date_from,
                                          second_date_to)
