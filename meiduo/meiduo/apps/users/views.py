from django.shortcuts import render
from django import http
from django.views import View
from django_redis import get_redis_connection
from users.models import User
import json
import re
#from django.contrib.auth import login
import logging
from django.contrib.auth import login,authenticate
logger = logging.getLogger('django')

# Create your views here.

class UsernameCountView(View):
    def get(self,request,username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':'訪問數據庫失敗'})

        return http.JsonResponse({'code':0,'errmsg':'ok','count':count})

class MobileCountView(View):
    def get(self,request,mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':'查詢數據出錯'})

        return http.JsonResponse({'code':0,'errmsg':'ok','count':count})

class RegisterView(View):
    def post(self,request):
        json_bytes = request.body
        json_str = json_bytes.decode()
        json_dict = json.loads(json_str)

        username = json_dict.get('username')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        mobile = json_dict.get('mobile')
        allow = json_dict.get('allow')
        sms_code = json_dict.get('sms_code')
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s'%mobile)
        if not all([username,password,password2,mobile,sms_code]):
            return http.JsonResponse({'code':400,'errmsg':'缺少必傳參數!'})

        if not re.match(r'^[a-zA-Z0-9]{5,20}$',username):
            return http.JsonResponse({'code':400,'errmsg':'password格式有誤'})

        if password !=password2:
            return http.JsonResponse({'code':400,'errmsg':'兩次輸入不一致'})

        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.JsonResponse({'code':400,'errmsg':'手機號格式有誤.....'})
        if not sms_code_server:
            return  http.JsonResponse({'code':400,'errmsg':'短信驗證碼失效'})
        if sms_code != sms_code_server.decode():
            return  http.JsonResponse({'code':400,'errmsg':'短信驗證碼錯誤'})

        if allow !=True:
            return http.JsonResponse({'code':400,'errmsg':'allow格式有誤'})
        try :
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)

        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':'註冊失敗!'})
        login(request,user)
        return  http.JsonResponse({'code':0,'errmsg':'註冊成功!'})


class LoginView(View):

    def post(self,request):
        data_dict = json.loads(request.body.decode())
        username = data_dict.get('username')
        password = data_dict.get('password')

        if not all([username,password]):
            return http.JsonResponse({'code':400,'errmsg':'參入傳入錯誤'})

        try:
            username = User.objects.get(username=username)

        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':e})

        user = authenticate(request,username=username,password=password)

        if not user:
            return http.JsonResponse({'code':400,'errmsg':'密碼錯誤'})

        login(request,user)
        return http.JsonResponse({'code':0,'errmsg':'OK'})