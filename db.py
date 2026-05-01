import settings
import mariadb
from functools import wraps
# __ 資料庫操作_________________________________________________________________
def db_transaction(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        conn = mariadb.connect(host=settings.HOST, port=settings.PORT,
                user=settings.USER, password=settings.PASSWORD,
                database=settings.DATABASE)
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