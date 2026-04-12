# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash
# from flask_mail import Mail, Message




# _______________________________________自定義模組_______________________________________
import settings
from models import Models
# from fool_proof import *


# _______________________________________初始化___________________________________________
app = Flask(__name__)



# ________________________________________API_____________________________________________

# ____templates file names____
# index.html
# register.html
# login.html
# member.html
# checkout.html
# cart.html
# manage.html


# @app.route("/...")
# def ...():
#     return


    
if __name__ == "__main__":
    """
    先於settings.py中設定APP_PORT
    """
    app.run(debug=True,use_reloader=False,port=settings.APP_PORT)