from django.shortcuts import render
from rest_framework.views import APIView
# Create your views here.
from .serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectAllSerializer
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework import status
import base64
import pickle
from . import constants
from goods.models import SKU


class CartViews(APIView):

    def perform_authentication(self, request):
        """
        重写父类的用户验证方法，不在进入视图前就检查JWT
        """
        pass

    def get(self, request):

        '''
        查询购物车数据,不需要反序列化
        '''
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 链接redis数据库
            redis_conn = get_redis_connection('cart')
            # 读取redis购物车中所有的sku_id和count（hash）
            # {
            #     b'sku_id_1':b'count_1',
            #     b'sku_id_2': b'count_2'
            # }

            redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)
            # 读物redis购物车中set里面所有的sku_id
            # [sku_id_1]
            redis_selected_set = redis_conn.smembers('selected_%s' % user.id)

            cart_dict = {}
            for sku_id, count in redis_cart_dict.items():

                cart_dict[int(sku_id)] = {
                    "count": int(count),
                    "selected": sku_id in redis_selected_set
                }


        else:
            cookie_cart_str = request.COOKIES.get('cart')

            if cookie_cart_str:
                cookie_cart_str_bytes = cookie_cart_str.encode()
                cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
                cart_dict = pickle.loads(cookie_cart_dict_bytes)
            else:
                cart_dict = {}
        # 统一的查询，因为数据都整合完了

        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)

        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        serializer = CartSKUSerializer(skus,many=True)
        return Response(serializer.data)

    def post(self, request):
        '''新增购物车数据'''
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        #验证用户是否登陆

        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 链接redis数据库
            redis_conn = get_redis_connection('cart')
            # 使用 管道
            pl = redis_conn.pipeline()
            # hincrby 哈希存入为哈希表 key 中的域 field 的值加上增量 increment 。

            # 增量也可以为负数，相当于对给定域进行减法操作。
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            #判断勾选
            if selected:
                # sadd 集合 将一个或多个 member 元素加入到集合 key 当中，已经存在于集合的 member 元素将被忽略
                pl.sadd('selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            # 用户未登录，在cookie中保存
            # {
            #     1001: { "count": 10, "selected": true},
            #     ...
            # }
            # 使用pickle序列化购物车数据，pickle操作的是bytes类型
            cookie_cart_str = request.COOKIES.get('cart')
            if cookie_cart_str is not None:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart_str.encode()))
            else:
                cookie_cart_dict = {}

            # 判断当前要存储的sku_id是否存在，如果存在就累加；反之直接新增
            if sku_id in cookie_cart_dict:
                origin_count = cookie_cart_dict[sku_id]['count']
                count += origin_count

            cookie_cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            new_cookie_cart_dict_bytes = pickle.dumps(cookie_cart_dict)
            new_cookie_cart_str_bytes = base64.b64encode(new_cookie_cart_dict_bytes)
            new_cookie_cart_str = new_cookie_cart_str_bytes.decode()

            #构造响应对象
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            #响应数据的同时将数据添加到cookie
            # 需要设置有效期，否则是临时cookie
            response.set_cookie('cart', new_cookie_cart_str, max_age=constants.CART_COOKIE_EXPIRES)
            # 响应
            return response

    def put(self, request):
        '''修改购物车数据'''
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 链接redis数据库
            redis_conn = get_redis_connection('cart')
            # 使用 管道
            pl = redis_conn.pipeline()
            # 修改redis中的hash里面的sku_id和count
            # 由于前后端约定数据的传输是幂等的方式，前端直接给我们传递最终的结果，所以后端直接覆盖写入
            pl.hset('cart_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)

            pl.execute()
            return Response(serializer.data)
        else:
            # 用户未登录，在cookie中保存
            # {
            #     1001: { "count": 10, "selected": true},
            #     ...
            # }
            # 使用pickle序列化购物车数据，pickle操作的是bytes类型
            cookie_cart_str = request.COOKIES.get('cart')
            if cookie_cart_str is not None:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart_str.encode()))
            else:
                cookie_cart_dict = {}

            cookie_cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            new_cookie_cart_dict_bytes = pickle.dumps(cookie_cart_dict)
            new_cookie_cart_str_bytes = base64.b64encode(new_cookie_cart_dict_bytes)
            new_cookie_cart_str = new_cookie_cart_str_bytes.decode()

            # 构造响应对象
            response = Response(serializer.data)
            # 响应数据的同时将数据添加到cookie
            # 需要设置有效期，否则是临时cookie
            response.set_cookie('cart', new_cookie_cart_str, max_age=constants.CART_COOKIE_EXPIRES)
            # 响应
            return response


    def delete(self, request):
        '''删除购物车数据'''
        # try:
        #     user = request.user
        # except Exception:
        #     user = None
        #
        # if user is not None and user.is_authenticated:
        #     # 链接redis数据库
        #     redis_conn = get_redis_connection('cart')
        #     # 读取redis购物车中所有的sku_id和count（hash）
        #     # {
        #     #     b'sku_id_1':b'count_1',
        #     #     b'sku_id_2': b'count_2'
        #     # }

        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')

        try:

            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
                # 链接redis数据库
            redis_conn = get_redis_connection('cart')
            # 读取redis购物车中所有的sku_id和count（hash）
            # {
            #     b'sku_id_1':b'count_1',
            #     b'sku_id_2': b'count_2'
            # }

            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            cookie_cart_str = request.COOKIES.get('cart')
            # 构造响应对象
            response = Response(status=status.HTTP_204_NO_CONTENT)
            if cookie_cart_str is not None:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart_str.encode()))

                new_cookie_cart_dict_bytes = pickle.dumps(cookie_cart_dict)
                new_cookie_cart_str_bytes = base64.b64encode(new_cookie_cart_dict_bytes)
                new_cookie_cart_str = new_cookie_cart_str_bytes.decode()
                # 响应数据的同时将数据添加到cookie
                # 需要设置有效期，否则是临时cookie

                response.set_cookie('cart', new_cookie_cart_str, max_age=constants.CART_COOKIE_EXPIRES)
            # 响应
            return response



class CartSelectAllView(APIView):

    def perform_authentication(self, request):
        """
        重写父类的用户验证方法，不在进入视图前就检查JWT
        """
        pass


    def put(self,request):
        serializer = CartSelectAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data['selected']

        try:

            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
                # 链接redis数据库
            redis_conn = get_redis_connection('cart')
            cart = redis_conn.hgetall('cart_%s' % user.id)
            sku_id_list = cart.keys()

            if selected:
                # 全选
                redis_conn.sadd('selected_%s' % user.id, *sku_id_list)

            else:
                redis_conn.srem('selected_%s' % user.id, *sku_id_list)
            return Response({'message': 'ok'})

        else:
            # cookie
            cart = request.COOKIES.get('cart')

            response = Response({'message': 'OK'})

            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
                for sku_id in cart:
                    cart[sku_id]['selected'] = selected
                cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                # 设置购物车的cookie
                # 需要设置有效期，否则是临时cookie
                response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)

            return response




