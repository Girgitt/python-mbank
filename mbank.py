# -*- coding:utf8 -*-
import re
import datetime
from mechanize import Browser
from pyquery import PyQuery as pq

# regex do wyciagania danych z history CSV
reg = re.compile('(?P<operation_date>^\d+\-\d+\-\d+);' \
                 '(?P<book_date>\d+\-\d+\-\d+);' \
                 '(?P<type>[^;]+);' \
                 '"(?P<title>[^;]*)";' \
                 '"(?P<who>[^;]+)";' \
                 '\'(?P<account>[^;]*)\';' \
                 '(?P<amount>[-\ 0-9,]+);' \
                 '(?P<account_balance>[-\ 0-9,]+);') 


def clean_amount(amount):
    return float(amount.replace(' ', '').replace(',', '.').replace('PLN',''))


def fixcoding(text):
    return text.decode('windows-1250').encode('utf8').decode('utf8')


def cvtdate(text, fmt='%Y-%m-%d'):
    return datetime.datetime.strptime(text, fmt).date()


class Mbank(object):
    """
    Glowna klasa realizujaca akcje logowania, przejscia na odpowiedni
    formularz i wykonywania pozadanych akcji na stronach panelu klienta
    mbanku.
    """
    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.url = 'https://www.mbank.com.pl'
        self.form_name = 'MainForm'

        self.br = Browser()
        # Ustawienie naglowkow (szczegolnie istotny Accept-Encoding)
        # bez ktorego nie pobraloby dane w postaci CSV/HTML.
        self.br.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (X11; U; Linux x86_64; ' \
             'pl-PL; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 ' \
             '(lucid) Firefox/3.6.6'),
            ('Accept-Encoding', 'gzip,deflate')
        ]

    def login(self):
        """
        Metoda realizujaca logowanie sie do panelu klienta mbanku.
        """
        now = datetime.datetime.now()
        formated_now = now.strftime('%a, %d %b %Y, %X').lower()
        self.br.open(self.url)
        self.br.select_form(name=self.form_name)
        self.br.form.set_all_readonly(False)
        self.br.form.set_value(name='customer', value=self.id)
        self.br.form.set_value(name='password', value=self.password)
        self.br.form.set_value(name='localDT', value=formated_now)
        return self.br.submit()

    def select(self, path, number):
        number = number.replace(' ','')
        self.br.open('%s/%s' % (self.url, path))
        for l in self.br.links():
            if l.text.replace(' ', '').find(number) > -1:
                break

        # Znajdz atrybut onclick dla taga <a> z numerem konta bankowego.
        onclick = None
        for a in l.attrs:
            if a[0] == 'onclick':
                onclick = a[1]
                break
        if not onclick:
            raise Exception('No onclick found')
        return self.onclick(onclick)

    def onclick(self, onclick):
        onclick = onclick.split("'")
        # Adres gdzie bedziemy slac dane.
        addr = onclick[1]
        # Metoda wysylania (POST)
        method = onclick[5]
        # Parametry
        params = onclick[7]

        self.br.select_form(name=self.form_name)
        self.br.form.action = '%s%s' % (self.url, addr)
        self.br.form.method = method
        # Aktywuj inputa __PARAMETERS (ma ustawiony status readonly)
        self.br.form.set_all_readonly(False)
        # Przypisz parametry
        self.br.form.set_value(name='__PARAMETERS', value=params)
        return self.br.submit()

    def get_credit_card_history(self, credit_card_number, start=None, end=None, full_credit_history=False):
        self.select('cards_list.aspx', credit_card_number)

        self.br.select_form(name=self.form_name)
        self.br.form.action = '%s%s' % (self.url, '/cc_historical_statements_list.aspx')
        self.br.form.method = 'POST'
        response = self.br.submit()
        doc = pq(response.read())
        history_start = [cvtdate(a.text) for a in doc('#historicalStatementsList p.Date span')]
        history_end = [cvtdate(a.text) for a in doc('#historicalStatementsList p.Date a')]
        history_onclick = [pq(a).attr.onclick for a in doc('#historicalStatementsList p.Date a')]
        history = zip(*[history_start, history_end, history_onclick])

        history_to_check = []
        if full_credit_history:
            for h in history:
                if h[1] == end:
                    history_to_check.append(h[2])
        else:
            for h in history:
                if h[0] <= start <= h[1]:
                    history_to_check.append(h[2])
                elif h[0] <= end <= h[1]:
                    history_to_check.append(h[2])
                elif start <= h[0] <= end:
                    history_to_check.append(h[2])
                elif start <= h[1] <= end:
                    history_to_check.append(h[2])

        for h in history_to_check:
            response = self.onclick(h)
            doc = pq(response.read())
            amount = [a.text for a in doc('#cc_current_operations p.Amount:eq(1) span')]
            title = [a.text for a in doc('#cc_current_operations p.Merchant span')]
            _type = [a.text for a in doc('#cc_current_operations p.OperationType a')]
            book_date = [a.text for a in doc('#cc_current_operations p.Date span:eq(1)')]
            operation_date = [a.text for a in doc('#cc_current_operations p.Date span:eq(0)')]

            row = zip(*[amount, title, _type, book_date, operation_date])
            for r in row:
		title = r[1]
                if r[2] == u'OP\u0141ATA ZA KART\u0118':
                    title = 'mBank'
                if not title:
                    continue
                yield {
                    'operation_date': cvtdate(r[4], '%d-%m-%Y'),
                    'book_date': cvtdate(r[3], '%d-%m-%Y'),
                    'type': ' '.join(r[2].split()),
                    'who': '',
                    'account': '',
                    'title': ' '.join(title.split()),
                    'amount': clean_amount(r[0]),
                    'account_balance': 0
                }

    def get_history(self, bank_number, start=None, end=None):
        """
        Glowna metoda uruchamiajaca w sobie przejscie na formularz
        historii transakcji (po zalogowaniu) i pobranie danych.
        """
        self.select('accounts_list.aspx', bank_number)
        self.br.select_form(name=self.form_name)
        self.br.form.action = '%s%s' % (self.url, '/account_oper_list.aspx')
        self.br.form.method = 'POST'
        self.br.submit()
        data = self._get_history(start, end)
        return self.parse_history_csv(data)

    def _get_history(self, start, end):
        """
        Metoda ustawiajaca odpowiednie parametry na formularzu historii
        transakcji i wysylajaca go.
        """
        self.br.select_form(name=self.form_name)
        # exportuj dane
        self.br.form.find_control("export_oper_history_check").items[0].selected = True
        # ustawienie selecta z typem danych (domyslnie HTML)
        self.br.form.set_value(name='export_oper_history_format', value=['CSV'])
        self.br.form.action = '%s%s' % (self.url, '/printout_oper_list.aspx')
        self.br.form.method = 'POST'

        self.br.form.set_value(['daterange_radio'], name='rangepanel_group')
        self.br.form.set_value(start.strftime('%d'), name='daterange_from_day')
        self.br.form.set_value(start.strftime('%m'), name='daterange_from_month')
        self.br.form.set_value(start.strftime('%Y'), name='daterange_from_year')

        self.br.form.set_value(end.strftime('%d'), name='daterange_to_day')
        self.br.form.set_value(end.strftime('%m'), name='daterange_to_month')
        self.br.form.set_value(end.strftime('%Y'), name='daterange_to_year')

        response = self.br.submit()
        return response.read()

    def parse_history_csv(self, data):
        """
        Przetworzenie danych historii transakcji w postaci CSV do
        dict().
        """
        for row in data.split('\n'):
            f = reg.search(row)
            if not f:
                continue
            parsed_row = reg.search(row).groupdict()
            yield {
                'operation_date': cvtdate(parsed_row['operation_date']),
                'book_date': cvtdate(parsed_row['book_date']),
                'type': ' '.join(fixcoding(parsed_row['type']).split()),
                'who': ' '.join(fixcoding(parsed_row['who']).split()),
                'account': fixcoding(parsed_row['account']),
                'title': ' '.join(fixcoding(parsed_row['title']).split()),
                'amount': clean_amount(parsed_row['amount']),
                'account_balance': clean_amount(parsed_row['account_balance'])
            }
