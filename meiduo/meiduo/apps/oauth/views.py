from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import  http
from django.views import View
from django.contrib.auth import login
import logging
import json,re
from django.db import DatabaseError

from carts.utils import merge_cart_cookie_to_redis
from users.models import User
from django_redis import get_redis_connection
from meiduo.utils.secret import SecretOauth
from . models import OAuthQQuer
logger = logging.getLogger('django')
# Create your views here.


class QQURLView(View):
    def get(self,request):

        next = request.GET.get('next')
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next
                        )

        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code':0,'errmsg':'OK','login_url':login_url})


class QQUserView(View):
    def get(self,request):

        code = request.GET.get('code')
        if not code:
            return http.JsonResponse({'code':400,'errmsg':'缺少code 參數'})

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            access_token = oauth.get_access_token(code)
            print(access_token)
            openid = oauth.get_open_id(access_token)
            print(openid)
        except Exception as e:
            logger.error(e)

            return http.JsonResponse({'code':400,'errmsg':'oauth2.0認證'})
        try:
            qq_user = OAuthQQuer.objects.get(openid=openid)
        except OAuthQQuer.DoesNotExist as e :
            auth = SecretOauth()
            access_token = auth.dumps({'openid':openid})
            print('access_token',access_token)
            return http.JsonResponse({
                'code': 300,
                'errmsg': 'ok',
                'access_token': access_token
                # 'access_token': <加密后的openid>
            })
        else :
            login(request, qq_user.user)
            response = http.JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('username', qq_user.user.username, max_age=14 * 24 * 60)
            return response
    def post(self,request):

        data_dict = json.loads(request.body.decode())
        mobile = data_dict.get('mobile')
        password = data_dict.get('password')
        sms_code_client = data_dict.get('sms_code')
        access_token = data_dict.get('access_token')

        if not all ([mobile,password,sms_code_client,access_token]):
            return http.JsonResponse({'code':400,'errmsg':'缺少必要參數'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '请输入正确的手机号码'})

            # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '请输入8-20位的密码'})

        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s'% mobile)

        if sms_code_server is None:
            return  http.JsonResponse({'code':'400','errmsg':'驗證碼失效'})

        if sms_code_client !=sms_code_server.decode():
            return http.JsonResponse({'code':400,'errmsg':'輸入的驗證碼有誤'})


        openid = SecretOauth().loads(access_token).get('openid')
        if not openid:
            return http.JsonResponse({'code':400,'errmsg':'缺少openid'})

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile,
                                            password=password,
                                            mobile=mobile)

        else:
            if not user.check_password(password):
                return http.JsonResponse({'code':400,'errmsg':'數據庫添加錯誤'})

        login(request,user)
        response = http.JsonResponse({'code':0,'errmsg':'OK'})

        response.set_cookie('username',
                            user.username,
                            max_age=3600*24*14)
        merge_cart_cookie_to_redis(request = request, response=response)
        return  response


