from django_redis import get_redis_connection

from meiduo.utils.cookiesecret import CookieSecret
def merge_cart_cookie_to_redis(request,response):
    user = request.user
    conn = get_redis_connection('carts')
    cart_cookie = request.COOKIES.get('carts')
    if cart_cookie:
        cart_cookie = CookieSecret.loads(cart_cookie)
    else:
        cart_cookie={}
    sku_ids = cart_cookie.keys()
    for sku_id in sku_ids:
        conn.hset('carts_%s'%user.id,sku_id,cart_cookie[sku_id]['count'])
        if cart_cookie[sku_id]['selected']:
            conn.sadd('selected_%s'%user.id,sku_id)
    response.delete_cookie('carts')
    return response

