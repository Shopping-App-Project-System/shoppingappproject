from settings import DB_HOST,DB_PORT,DB_USER,DB_PASSWORD,DB_DATABASE
import pymysql
from functools import wraps
# __ 資料庫操作_________________________________________________________________
def db_transaction(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        conn = pymysql.connect(host=DB_HOST, port=DB_PORT,
                user=DB_USER, password=DB_PASSWORD,
                database=DB_DATABASE)
        cursor = conn.cursor(dictionary=True)
        try:
            result = fun(cursor,*args,**kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    return wrap