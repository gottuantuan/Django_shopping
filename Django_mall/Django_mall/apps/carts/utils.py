import base64
import pickle
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """登录时合并cookie购物车数据到redis：在登录时被调用"""

    # 读取cookie中的购物车数据
    cookie_cart_str = request.COOKIES.get('cart')

    # 如果cookie中没有购物车记录，就直接返回，不去执行合并操作
    if not cookie_cart_str:
        return response

    #读取出cookie中已经存在的购物车数据

    cookie_cart_str_bytes = cookie_cart_str.encode()
    cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
    cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)


    redis_conn = get_redis_connection('cart')

    redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)
    redis_cart_selected = redis_conn.smembers('selected_%s' % user.id)

    new_redis_cart_dict = {}

    for sku_id, count in redis_cart_dict.items():
        new_redis_cart_dict[int(sku_id)] = int(count)

        # 遍历cookie中的购物车数据，合并到redis (核心代码)
    for sku_id, cart_dict in cookie_cart_dict.items():
        new_redis_cart_dict[sku_id] = cart_dict['count']

        if cart_dict['selected']:
            redis_cart_selected.add(sku_id)

    pl = redis_conn.pipeline()
    pl.hmset('cart_%s' % user.id, new_redis_cart_dict)
    pl.sadd('selected_%s' % user.id, *redis_cart_selected)
    pl.execute()

    # 清空cookie
    response.set_cookie('cart')

    # 只有返回了响应对象，cookie才有机会被执行的
    return response