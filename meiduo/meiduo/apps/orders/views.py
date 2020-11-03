import json
from _decimal import Decimal

from django import http
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
# Create your views here.
from django.utils import timezone
from django.views import View
from django_redis import get_redis_connection

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from users.models import Address
from users.utils import LoginRequiredJSONMixin


class OrderSettlementView(LoginRequiredJSONMixin,View):
    def get(self,request):
        user = request.user
        conn = get_redis_connection('carts')
        selected_list = conn.smembers('selected_%s'%user.id)
        carts_dict = conn.hgetall('carts_%s'%user.id)
        sku_ids = carts_dict.keys()

        skus = []
        for sku_id in sku_ids:
            if sku_id in selected_list:
                sku = SKU.objects.get(pk = sku_id.decode())
                skus.append({
                      'id':sku.id,
                      'name':sku.name,
                      'default_image_url':sku.default_image.url,
                      'count':int(carts_dict[sku_id]),
                      'price':sku.price,
                  })
        addresses = []
        address_objests = Address.objects.filter(user=user.id,is_deleted=False)
        for address_objest in address_objests:
            addresses.append({
                'id':address_objest.id,
               'province':address_objest.province.name,
                'city':address_objest.city.name,
                'district':address_objest.district.name,
                'place':address_objest.place,
                'mobile':address_objest.mobile,
                'receiver':address_objest.receiver
            })

        freight = Decimal('10.00')
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'context':{
                'addresses':addresses,
                'skus':skus,
                'freight':freight,
            }
        })

class OrderCommitView(LoginRequiredJSONMixin,View):
    def post(self,request):
        user = request.user
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('ay_method')
        if not all([pay_method,address_id]):
            return http.HttpResponse('缺少必要參數')

        try:
            address = Address.objects.get(pk = address_id)
        except Address.DoesNotExist as e:
            return JsonResponse({'code':400,'errmsg':'地址錯誤'})

        if not pay_method in [OrderInfo.PAY_METHODS_ENUM['CASH'],OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code':400,'errmsg':'不存在的支付方式'})

        cur_time = timezone.localtime()
        order_id = cur_time.strftime('%Y%m%d%H%M%S')+"%06d"%user.id

        #讀取用戶的購物車商品數據:
        conn = get_redis_connection('carts')
        redis_selected = conn.smembers('selected_%s'%user.id)
        redis_carts = conn.hgetall('carts_%s'%user.id)
        cart_dict = {}
        for k,v in redis_carts.items():
            if k in redis_selected:
                cart_dict[int(k)] = {
                    'count':int(v),
                    'selected':True,

                }
        with transaction.atomic():
            save_id = transaction.savepoint()
            order = OrderInfo.objects.create(
                order_id = order_id,
                user = user,
                address = address,
                total_count=0,
                total_amount=0,
                freight = Decimal('10.00'),
                pay_method = pay_method,
                status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            )

            sku_ids = cart_dict.keys()
            for sku_id in sku_ids:
                sku = SKU.objects.get(pk = sku_id)
                old_stock = sku.stock
                old_sales = sku.sales
                count = cart_dict[sku_id]['count']

                if count > old_stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'code':400,'errmsg':'庫存不足'})

                sku.stock -=count
                sku.sales +=count

                sku.save()
                sku.spu.sales += count
                sku.spu.save()

                order.total_count +=count
                order.total_amount += sku.price*count

                OrderGoods.objects.create(
                    order = order,
                    sku = sku,
                    count = count,
                    price = sku.price
                )

                order.total_amount +=Decimal(10.0)
                order.save()

                transaction.savepoint_commit(save_id)

            sku_ids = cart_dict.keys()
            p = conn.pipeline()
            p.hdel('carts_%s'%user.id, *sku_ids)
            p.srem('seleceted_%s'%user.id, *sku_ids)
            p.execute()

            return  JsonResponse({'code':0,'errmsg':'ok','order_id':order_id})



