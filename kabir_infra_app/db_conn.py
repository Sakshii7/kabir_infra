import xmlrpc.client

from utils import Environment

url = Environment.get("HOST_URL")
db = Environment.get("DATABASE_NAME")
username = Environment.get("DATABASE_USERNAME")
password = Environment.get("DATABASE_PASSWORD")
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url), allow_none=True)


class DbConn:
    @staticmethod
    def get(*args):
        return models.execute_kw(db, uid, password, *args)
