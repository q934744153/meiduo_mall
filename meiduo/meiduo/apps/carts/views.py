from django.shortcuts import render
from django.views import View
import json
from django.http import *
# Create your views here.
from django_redis import get_redis_connection

from goods.models import SKU
from meiduo.utils.cookiesecret import CookieSecret


class AddToCarts(View):
    def post(self,request):
        user = request.user
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected',True)
        conn = get_redis_connection('carts')
        if not all ([sku_id,count]):
            return HttpResponse('缺少必要參數')
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponse('商品不存在')

        if user.is_authenticated:

            redis_carts = conn.hgetall('carts_%s'%user.id)
            redis_selected = conn.smembers('selected_%s'%user.id)
            if str(sku_id).encode() in redis_carts:
                count = count + int(redis_carts[str(sku_id).encode()])
                conn.hset('carts_%s'%user.id,sku_id,count)
            else:
                conn.hset('carts_%s' % user.id, sku_id, count)
            if selected:
                conn.sadd('selected_%s' % user.id, sku_id)
            return  JsonResponse({
                'code':0,
                'errmsg':'ok',

            })
        else:
              cart_str = request.COOKIES.get('carts')

        if cart_str:
            cart_dict = CookieSecret.loads(cart_str)

        else:
            cart_dict = {}

        if sku_id in cart_dict:
            cart_dict[sku_id]['count'] +=count
            cart_dict[sku_id]['selected'] = selected
        else:
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }

        cart_dict = CookieSecret.dumps((cart_dict))

        response = JsonResponse({'code':0,'errmsg':'ok'})
        response.set_cookie('carts',cart_dict,max_age=24*30*3600)

        return response

    def get(self,request):
        if request.user.is_authenticated:
            conn = get_redis_connection('carts')
            sku_dict = conn.hgetall('carts_%s'%request.user.id)
            selected_list = conn.smembers('selected_%s'%request.user.id)
            cart_dict = {}
            for sku_id,count in sku_dict.items():
                sku_id = sku_id.decode()
                count = count.decode()
                cart_dict[sku_id] = {
                    'count':count,
                    'selected':  sku_id.encode() in selected_list
                }
        else:
            cart_byte = request.COOKIES.get('carts')
            cart_dict = CookieSecret.loads(cart_byte)
        cart_skus = []
        for sku_id in  cart_dict:
            sku = SKU.objects.get(pk = sku_id)
            cart_skus.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'price':sku.price,
                'count':cart_dict[sku_id]['count'],
                'selected':cart_dict[sku_id]['selected'],
            })
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'cart_skus':cart_skus,
        })

    def put(self,request):
        user = request.user
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        print(count,type(count))
        selected = json_dict.get('selected',True)
        if not all([sku_id,count]):
            return HttpResponse('缺少必要參數')
        try:
            sku = SKU.objects.get(id = sku_id)
        except Exception:
            return HttpResponse('商品不存在')
        # try:
        #     count = int(count)
        # except Exception:
        #     return  HttpResponse('參數count有誤')
        if selected:
            if not isinstance(selected,bool):
                return  HttpResponse('參數selected有誤')
        if user.is_authenticated:
            conn = get_redis_connection('carts')
            selected_list = conn.smembers('selected_%s'%user.id)
            # cart_dict = conn.hgetall('carts_%s' % user.id)
            # cart_dict['sku_id'] = count
            # print(cart_dict)
            conn.hset('carts_%s'%user.id,sku_id,count)
            cart_dict = conn.hgetall('carts_%s' % user.id)
            print(cart_dict)
            if selected:
                conn.sadd('selected_%s'%user.id,sku_id)
            else:
                conn.srem('selected_%s'%user.id,sku_id)
            sku = SKU.objects.get(pk = sku_id)

            response = JsonResponse({
                'code':0,
                'errmsg':'ok',
                'cart_sku':{
                    'id': sku.id,
                    'count': count,
                    'selected': selected,
                    'name': sku.name,
                    'default_image_url': sku.default_image.url,
                    'price': sku.price,
                    'amount': sku.price * count
                }
            })
            return response
        else:
            cart_data = request.COOKIES.get('carts')
            if cart_data:
                cart_dict = CookieSecret.loads(cart_data)
            else: cart_dict = {}
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }
            cart_dict_str = CookieSecret.dumps(cart_dict)
            cart_sku = {
                'id':sku_id,
                'count':count,
                'selected':selected,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'price':sku.price,
                'amount':sku.price * count,
            }
            response = JsonResponse({'code':0,'errmsg':'ok','cart_sku':cart_sku})
            response.set_cookie('carts',cart_dict_str,max_age=24*3600)
            return response

#購物車的傷處
    def delete(self,request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        user = request.user
        try:
            SKU.objects.get(id = sku_id)
        except Exception:
            return  HttpResponse('商品不存在')

        if user.is_authenticated:
            conn = get_redis_connection('carts')
            cart_dict = conn.hgetall('carts_%s'%user.id)
            conn.hdel('carts_%s'%user.id,sku_id)
            conn.srem('selected_%s'%user.id,0,sku_id)
            return JsonResponse({'code':0,'errmsg':'OK'})


        else:
            cart_data = request.COOKIES.get('carts')
            if cart_data:
                cart_dict = CookieSecret.loads(cart_data)

            else:
                cart_dict = {}

            if sku_id in cart_dict:
                del cart_dict[sku_id]

                response = JsonResponse({
                    'code':0,
                    'errmsg':'ok',
                })
                carts = CookieSecret.dumps(cart_dict)

                response.set_cookie('carts',carts)

                return response

class AllSeleCart(View):
    def put(self,request):
        user = request.user
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')

        if not isinstance(selected,bool):
            return HttpResponse('參數錯誤')

        if user.is_authenticated:
            conn = get_redis_connection('carts')
            selected_list = conn.smembers('selected_%s'%user.id)
            carts_dict = conn.hgetall('carts_%s'%user.id)
            sku_ids = carts_dict.keys()
            if selected:
                conn.sadd('selected_%s'%user.id,*sku_ids)
            else:
                conn.srem('selected_%s'%user.id,*sku_ids)

            return JsonResponse({'code':0,'errmsg':'ok'})

        else:
            carts_data = request.COOKIES.get('carts')
            carts_dict = CookieSecret.loads(carts_data)

            for sku in carts_dict:
                carts_dict[sku]['selected'] = selected

            carts_dict = CookieSecret.dumps(carts_dict)

            response = JsonResponse({'code':0,'errmsg':'ok'})
            response.set_cookie('carts',carts_dict,24*30*3600)
            return  response


class CartsSimpleView(View):
    def get(self,request):
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('carts')
            sku_redis = conn.hgetall('carts_%s'%user.id)
            sku_ids = sku_redis.keys()
            selected_list = conn.smembers('selected_%s'%user.id)

            cart_skus = []
            for sku_id in sku_ids:
                if sku_id in selected_list:
                    cart_skus.append({
                        'id':sku_id.decode(),
                        'name':SKU.objects.get(pk = sku_id.decode()).name,
                        'count': int(sku_redis[sku_id]),
                        'default_image_url':SKU.objects.get(pk = sku_id.decode()).default_image.url,

                    })

        else:
            carts_cookies = request.COOKIES.get('carts')
            carts_cookies = CookieSecret.loads(carts_cookies)
            cart_skus = []
            for sku_id in carts_cookies:
                if carts_cookies[sku_id]['selected']:
                    cart_skus.append({
                        'id': sku_id,
                        'name':SKU.objects.get(pk=sku_id).name,
                        'count':carts_cookies[sku_id]['count'],
                        'default_image_url':SKU.objects.get(pk = sku_id).default_image.url,
                    })

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'cart_skus':cart_skus,
        })