from django import http
from django.views import View
from django_redis import get_redis_connection

from meiduo.utils.secret import SecretOauth
from users.models import User
from .models import Address
import json
import re
import logging
from django.contrib.auth import login,logout,authenticate
from users.utils import LoginRequiredJSONMixin,generate_verify_email_url
from celery_tasks.email.tasks import send_verify_email
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
        remembered = data_dict.get('remembered')
        if not all([username,password]):
            return http.JsonResponse({'code':400,'errmsg':'參入傳入錯誤'})
        """
        try:
            user = User.objects.get(username=username)

        except User.DoesNotExist as e:
            return http.JsonResponse({'code':400,'errmsg':e})


        if not user.check_password(password):
            return http.JsonResponse({'code':400,'errmsg':'密碼錯誤'})
        """
        user = authenticate(request,username=username,password=password)
        if not user:
            return http.JsonResponse({'code': 400, 'errmsg': '用户名或者密码错误'})

        login(request,user)
        if remembered != True:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

       # response = http.JsonResponse({'code':0,'errmsg':'OK'})
       # response.set_cookie('username',username,max_age=3600*24*14)
        #return response
        #response = http.JsonResponse.set_cookie('username',username,3600*24*14)
        response = http.JsonResponse({'code':0,'errmsg':'OK'})
        response.set_cookie('username',username,max_age=3600*24*14)
        return response

class LogoutView(View):

    def delete(self,request):

        logout(request)
        response = http.JsonResponse({'code':0,'errmsg':'ok'})
        response.delete_cookie('username')

        return response

class UserInfoView(LoginRequiredJSONMixin,View):

    """  def get(self,request):
        user = request.user
        if not user.is_authenticated:
            return http.JsonResponse({'code':400,'errmsg':'未登陆！'})
        return http.JsonResponse({

            'code':0,
            'errmsg':'ok',
            'info_data':{
                'username':user.username,
                'mobile':user.mobile,
                'email':user.email
            }
        })
        """
    def get(self,request):
        user = request.user
        return http.JsonResponse({

            'code': 0,
            'errmsg': 'ok',
            'info_data': {
                'username': user.username,
                'mobile': user.mobile,
                'email': user.email,
                'email_active':request.user.email_active,
            }
        })

class EmailView(LoginRequiredJSONMixin,View):

    def put(self,request):
        email = request.body.decode()
        email = json.loads(email)
        email = email.get('email')

        if not email:
            return http.JsonResponse({'code':400,'errmsg':'沒有傳入郵箱'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code':400,'errmsg':'郵箱不符合規範'})

        try:
            request.user.email=email
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code':'400','errmsg':'添加郵箱失敗'})



        verify_url = generate_verify_email_url(request)
        send_verify_email.delay(email,verify_url=verify_url)

        return http.JsonResponse({'code':0,'errmsg':'OK'})

        #ZEZMQOQSTHKDAJOC  郵箱鑰匙

class VerifyEmailView(View):

    def put(self,request):
        token = request.GET.get('token')
        if not token:
            return http.JsonResponse({'code':400,'errmsg':'驗證錯誤'})

        data_dict = SecretOauth().loads(token)
        try:
            user = User.objects.get(pk=data_dict.get('user_id'), email=data_dict.get('email'))
        except Exception as e:
            print(e)
            return http.JsonResponse({'code': 400, 'errmsg': '参数有误!'})

            # - 5.修改激活状态
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            return http.JsonResponse({'code': 0, 'errmsg': '激活失败!'})

        return http.JsonResponse({'code': 0, 'errmsg': '激活成功!'})


class AddAddress(View):
    def post(self,request):
        count = Address.objects.filter(user=request.user,is_deleted=False).count()
        if count>=20:
            return http.JsonResponse({'code': 400, 'errmsg': '超过地址数量上限'})

        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver,province_id,city_id,district_id,place,mobile]):
            return http.JsonResponse({'code': 400, 'errmsg':'缺少必要參數'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({'code': 400, 'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
                return http.JsonResponse({'code': 400, 'errmsg': '参数email有误'})
            return http.JsonResponse({'code': 400, 'errmsg':'參數錯誤'})


        try:
            address = Address.objects.create(
                user =request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel or '',
                email = email or '',
                )
            if not request.user.default_address:
                request.user.default_address=address
                request.user.save()

        except Exception as e :
            return http.JsonResponse({'code': 400, 'errmsg': '新增地址失败'})

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return http.JsonResponse({'code': 0, 'errmsg': '新增地址成功', 'address': address_dict})

class AddressShow(View):

    def get(self,request):
        user = request.user
        address_object = Address.objects.filter(user = user,is_deleted=False)
        address_list=[]
        for address in address_object:
            address_dict={
                "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email}
            if address.id == user.default_address_id:
                address_list.insert(0,address_dict)
            else:
                address_list.append(address_dict)


        return http.JsonResponse({'code':0,'errmsg':'ok',
                                  'default_address_id':user.default_address_id,
                                  'addresses':address_list})


class Update_address(LoginRequiredJSONMixin,View):

    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')


        if not all([receiver,province_id,city_id,district_id,place,mobile]):
            return  http.JsonResponse({'code':400,'errmsg':'缺少參數'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({'code': 400, 'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
                return http.JsonResponse({'code': 400, 'errmsg': '参数email有误'})
            return http.JsonResponse({'code': 400, 'errmsg':'參數錯誤'})

        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e :
            return http.JsonResponse({'code':400,'errmsg':'修改失敗'})
        address = Address.objects.get(id=address_id)
        return http.JsonResponse({
            'code':0,
            'errmsg':'OK',
            'address': {
            'receiver':address.receiver,
            'province': address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
            }})
    def delete(self,request,address_id):
        try:
            add_object = Address.objects.get(id=address_id)
            add_object.is_deleted = True
            add_object.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':400,'errmsg':'刪除失敗'})

        return http.JsonResponse({'code':0,'errmsg':'ok'})

class Default_Address(LoginRequiredJSONMixin,View):
    def put(self,request,address_id):
        user = request.user
        try:
            address = Address.objects.get(id=address_id)
            user.default_address = address
            user.save()
        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':'參數錯誤'})
        return http.JsonResponse({'code': 0, 'errmsg': 'ok'})


class SetTitle(View):
    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        if not all(title):
            return http.JsonResponse({'code':400,'errmsg':'缺少參數'})
        try:
            address = Address.objects.get(id = address_id)
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':400,'errmsg':'數據庫錯誤'})

        return http.JsonResponse({'code':0,'errmsg':'OK'})

class UpdatePassword(LoginRequiredJSONMixin,View):
    def put(self,request):
        json_dict = json.loads(request.body.decode())
        old_password = json_dict.get('old_password')
        new_password = json_dict.get('new_password')
        new_password2 = json_dict.get('new_password2')
        if not all([new_password2,new_password,old_password]):
            return http.JsonResponse({"code":400,'errmsg':'缺少參數'})

        if new_password !=new_password2:
            return  http.JsonResponse({'code':400,'errmsg':'兩次密碼補一致'})

        user = request.user
        if not user.check_password(old_password):
            return http.JsonResponse({'code':40,'errmsg':'密碼錯誤'})

        if not re.match(r'^[0-9a-zA-Z]{8,20}$',new_password):
            return  http.JsonResponse({"code":400,'errmsg':'密碼格式錯誤'})

        try:
            user.set_password(new_password)
            user.save()
        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':'數據庫錯誤'})

        logout(request)

        return http.JsonResponse({'code':0,'errmsg':'ok'})




