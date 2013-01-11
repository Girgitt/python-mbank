import requests


class BuxferConnection(object):
    url = "https://www.buxfer.com/api/"

    def __init__(self, user, password):
        response = requests.post(self.url + 'login.json',
                                 params={'userid':user,
                                         'password':password})
        self.token = response.json()['response']['token']

    def insert(self, t):
        params = {'token': self.token}
        params['format'] = 'sms'
        t['date'] = t['date'].strftime('%d-%m-%Y')
        t['title'] = t['description']
        t['amount'] = str(t['amount'])
        if t['amount'].startswith('-'):
            t['amount'] = t['amount'][1:]
        else:
            t['amount'] = '+%s' % t['amount']
        params['text'] = '%s %s acct:%s date:%s tags:%s status:pending' % (t['title'], t['amount'], t['accounts'], t['date'], t['tags'])
        return requests.post(self.url + 'add_transaction.json', params=params)
