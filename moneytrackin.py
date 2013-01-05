import hashlib
import requests
from requests.auth import HTTPBasicAuth


class MoneyTrackinConnection(object):
    url = 'https://www.moneytrackin.com/api/rest/%s'

    def __init__(self, user, password):
        m = hashlib.md5()
        m.update(password)
        password = m.hexdigest()
        self.auth = HTTPBasicAuth(user, password)

    def insert(self, transaction):
        return requests.get(self.url % 'insertTransaction', params=transaction, auth=self.auth)
