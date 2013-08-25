from common.config import *
import MySQLdb


def connect_db():
    return MySQLdb.connect(host=DB_HOST,
                           port=DB_PORT,
                           user=DB_USER,
                           passwd=DB_PASSWD,
                           charset='utf8',
                           db=DB_DB)
