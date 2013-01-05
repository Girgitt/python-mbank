============
Python mBank
============

Skrypt pobierający historię transakcji z mBanku (dla kont oraz kart kredytowych)

Przykład użycia dla konta::
    >>> import datetime
    >>> from mbank import Mbank
    >>> mbank = Mbank('identyfikator', 'haslo')
    >>> mbank.login()
    >>> start = datetime.date(2012,12,1)
    >>> end = datetime.date(2012,12,31)
    >>> transactions = mbank.get_history('54 1140 2004 0000 0000 0000 0000',
    ...                                  start=start, end=end)
    >>> for t in transactions:
    ...     print t
    {'account': u'834353458854333300000',
     'account_balance': 1000.00,
     'title': u'Przelew do ZUS',
     'book_date': datetime.date(2012, 12, 10),
     'type': u'PRZELEW PRZYSZ\u0141Y DO ZUS',
     'who': u'ZAK\u0141AD UBEZPIECZE\u0143 SPO\u0141ECZNYCH',
     'operation_date': datetime.date(2012, 12, 10),
     'amount': -600.00}

Dla karty kredytowej sytuacja wygląda podobnie::
    >>> transactions = mbank.get_credit_card_history('VISA CLASSIC CREDIT 4483 **** **** 0000',
    ...                                              start=start, end=end)
    >>> for t in transactions:
    ...     print t
    {'account': '', #always empty
     'account_balance': 0, #always 0
     'title': 'PKN STACJA PALIW',
     'book_date': datetime.date(2012, 12, 3),
     'type': u'ZAKUP PRZY U\u017bYCIU KARTY W KRAJU',
     'who': '', # always empty
     'operation_date': datetime.date(2012, 12, 1),
     'amount': -105.12}
