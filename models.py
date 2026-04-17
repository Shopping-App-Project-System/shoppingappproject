import mariadb
from functools import wraps
import settings


def start(fun):
    @wraps(fun)
    def wrap(self,*args,**kwargs):
        conn = mariadb.connect(host=self.HOST, port=self.PORT,
                user=self.USER, password=self.PASSWORD,
                database=self.DATABASE)
        cursor = conn.cursor()
        try:
            result = fun(self,cursor,*args,**kwargs)
            conn.commit()
            return result
        except Exception as e:
            raise e
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return wrap

class Models:
    def __init__(self):
        self.HOST = settings.HOST
        self.PORT = settings.PORT
        self.USER = settings.USER
        self.PASSWORD = settings.PASSWORD
        self.DATABASE = settings.DATABASE
    
    @start
    def createUser(self,cursor,user_name,user_account,user_password,user_mobile,user_email,user_address):
        cursor.execute(f"""
                                INSERT INTO `{settings.BRANCH_A_TABLE}`
                                (`user_name`,`user_account`,`user_password`,`user_mobile`,`user_email`,`user_address`)
                                VALUES (?,?,?,?,?,?)
                            """,(user_name,user_account,user_password,user_mobile,user_email,user_address))
    

    @start
    def updateUser(self, cursor, set_: dict, where: dict):
        set_key, set_value = tuple(set_.keys()), tuple(set_.values())
        where_key, where_value = tuple(where.keys()), tuple(where.values())
    
        set_sql = ", ".join(f"`{key}` = ?" for key in set_key)
        where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)
    
        cursor.execute(f"""
                            UPDATE `{settings.BRANCH_A_TABLE}`
                            SET {set_sql}
                            WHERE {where_sql}
                        """, set_value + where_value)
    @start
    def getUser(self, cursor, where: dict, *selections):
        where_key, where_value = tuple(where.keys()), tuple(where.values())
    
        if selections == ():
            selections = "*"
        else:
            selections = ",".join(f"`{selection}`" for selection in selections)
    
        where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)
    
        cursor.execute(f"""
                            SELECT {selections}
                            FROM `{settings.BRANCH_A_TABLE}`
                            WHERE {where_sql}
                        """, where_value)
    
        users = cursor.fetchall()
        if users != []:
            users = users[0]
            if len(users) == 1:
                return users[0]
            return users
        return None
    
                
if __name__ == "__main__":
    ...