from collections.abc import Callable, Iterable, Mapping
import json
import os
import io
from typing import Any
from functools import wraps
from flask import Flask, render_template, redirect, request, send_file, abort, Response
import random
import traceback
import sys
from logger import handler, DETAIL
from flasgger import Swagger
from folders import ROOTDIR, STATIC, TEMPLATES, OUTPUT
from logger import getLogger
import userM
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

admin = {
    'windowFlag':{},
    'ver':"?ver={:0>4d}".format(int(random.random()*10000)),
}

server = Flask(__name__, static_folder=STATIC, template_folder=TEMPLATES,static_url_path="/")

# login setting
# make key
server.config['SECRET_KEY'] = os.urandom(16).hex()

# https://ithelp.ithome.com.tw/articles/10224408
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.session_protection = "strong"
login_manager.login_view = 'login'
login_manager.login_message = 'please login.'

class User(UserMixin):
    """簡單繼承，以利後續擴充。
    
    from -> https://hackmd.io/@shaoeChen/ryvr_ly8f?type=view"""
    def __init__(self,ID,NAME,GROUP,**kargs) -> None:
        super().__init__()
        self.id = ID
        self.name = NAME
        self.group = GROUP

def loadUser(id):
    """使用 id 當作 key ，
    
    找不到 key 回傳 None 。"""
    userData = userM.User.get(id)
    if not userData: return

    user = User(**userData.__dict__)
    return user

def paswordCheck(id, passwprd):
    userData:userM.User = userM.User.get(id)
    return userData.PASSWORD == passwprd

@login_manager.user_loader  
def user_loader(email):  
    """  
 設置二： 透過這邊的設置讓flask_login可以隨時取到目前的使用者id   
 :param email:官網此例將email當id使用，賦值給予user.id    
 """
    return loadUser(email)

@login_manager.request_loader
def request_loader(request):
    id = request.values.get('email')
    password = request.values.get('password')
    user = loadUser(id)
    user.is_authenticated = (paswordCheck(id,password))

    return user


# 設定 SWAGGER
server.config['SWAGGER'] = {
    "title": "ServerM API",
    "description": "ServerM API",
    "version": "1.0.1",
    "termsOfService": "",
    "hide_top_bar": True
}

Swagger(server)

# 設定 logger
server.logger = getLogger(__name__)

def jsonifyPlus(data):
    """轉換順序不變的 json 。"""
    return Response(json.dumps(data), mimetype='application/json; charset=utf-8')

def popfile(path):
    """將檔案於硬碟刪除，儲存於記憶體中回傳"""
    # 將檔案暫存於記憶體中
    return_data = io.BytesIO()
    with open(path, 'rb') as fo:
        return_data.write(fo.read())
    return_data.seek(0)

    # 於硬碟刪除檔案
    os.remove(path)
    return return_data


@server.errorhandler(404)
def error404(e):
    """可以 catch 住所有 abort(404) 以及找不到對應 router 的處理請求。"""
    for key, value in e.__dict__.items():
        print(f'{key}: {value}')
    response = dict(message=e.description, error_code= e.code)
    return jsonifyPlus(response), e.code

@server.errorhandler(500)
def error500(e):
    error_class = e.__class__.__name__ # 引發錯誤的 class
    try:
        detail = e.args[-1] # 得到詳細的訊息
    except:
        detail = ''
    cl, exc, tb = sys.exc_info() # 得到錯誤的完整資訊 Call Stack
    lastCallStack = traceback.extract_tb(tb)[-1] # 取得最後一行的錯誤訊息
    fileName = lastCallStack[0] # 錯誤的檔案位置名稱
    lineNum = lastCallStack[1] # 錯誤行數 
    funcName = lastCallStack[2] # function 名稱
    # generate the error message
    # return 500 code
    response = {'errorType':error_class,
                'errorPoint':f"[{funcName}] {fileName}:{lineNum}",
                'detail':detail}
    
    server.logger.error(f'{error_class} at [{funcName}]\n{fileName}:{lineNum}\n{detail}')

    return jsonifyPlus(response), 500

class MyError(Exception):
    """自訂義"""
    pass

@server.errorhandler(MyError)
def MyErrorHandle(error):
    response = dict(status=0, message="400 Error", detiles = error)
    return jsonifyPlus(response), 400

# 設定檢查 url 參數 func
def varGetter(key:str,default='NooooDafault',typeInt:bool=False):
    NOFIND = 'NooooDafault'
    if typeInt: varType = int
    else: varType = str
    urlVarValue = request.args.get(key, default = default, type = varType)
    if urlVarValue == NOFIND: return False
    else: return urlVarValue

def verify_token(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper

@server.before_request
def log_request_info():
    pass

@server.after_request
def add_header(response):
    server.logger.debug(f'{request.host} - {request.method} {request.path} {request.environ.get("SERVER_PROTOCOL")} {response.status_code}')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['charset'] = 'utf-8'
    return response