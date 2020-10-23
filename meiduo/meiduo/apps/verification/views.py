from django.shortcuts import render
from celery_tasks.sms.tasks import ccp_send_sms_code
# Create your views here.

import random
from django.views import View
from django import http
from django_redis import get_redis_connection
from .libs.captcha import captcha
from .libs.yuntongxun.ccp_sms import CCP
class ImageCodeView(View):
    def get(self,request,uuid):
        text,image = captcha.captcha.generate_captcha()
        #text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s'%uuid,300,text)

        return http.HttpResponse(image,content_type='image/jpg')



class SMCodeView(View):
 def get(self,request,mobile):
     image_code_client = request.GET.get('image_code')
     uuid = request.GET.get('image_code_id')
     if not all([image_code_client,uuid]):
         return http.JsonResponse({'code':400,
                                   'errmsg':'缺少必傳參數'})
     redis_conn = get_redis_connection('verify_code')
     image_code_server = redis_conn.get('img_%s'%uuid)
     redis_conn.delete('img_%s'% uuid)
     if image_code_server is None:
         return http.JsonResponse({'code':400,'errmsg':'圖形驗證碼已經失效'})
     try:
         redis_conn.delete('img_%s'%uuid)
     except Exception as e:
         print(e)

     image_code_server = image_code_server.decode()

     if image_code_server.lower() != image_code_client.lower():
         return http.JsonResponse({'code':400,'errmsg':'輸入圖形驗證碼有誤'})

     #redis_conn.setex('send_flag_%s' % mobile,60,1)
     send_flag = redis_conn.get('send_flag_%s'%mobile)
     if send_flag:
         return  http.JsonResponse({"code":400,'errmsg':'發送短信國語頻繁'})
     sms_code = '%06d'%random.randint(0,999999)
     #logger.info(sms_code)
     pl = redis_conn.pipeline()
     pl.setex('sms_%s'%mobile,
                      300,
                      sms_code)

     #CCP().send_template_sms(mobile,[sms_code,5],1)
     ccp_send_sms_code.delay(mobile,sms_code)
     print('短信驗證碼',sms_code)
     pl.setex('send_flag_%s' % mobile, 60, 1)
     pl.execute()
     return  http.JsonResponse({'code':0,'errmsg':'發送短信成功'})
