from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
# Create your views here.
from .models import OAuthQQUser
from rest_framework_jwt.settings import api_settings
from rest_framework.views import APIView
from .utils import QQOauth

from rest_framework.response import Response
from .exceptions import QQAPIException
from . import serializer
import logging

logger = logging.getLogger('django')


# "login_url": "https://graph.qq.com/oauth2.0/show?which=Login&display=pc&response_type=code&client_id=101474184&redirect_uri=http%3A%2F%2Fwww.meiduo.site%3A8080%2Foauth_callback.html&state=%2F&scope=get_user_info"
#  url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
class QQAuthURLView(APIView):
    """提供用户用于登录到QQ服务器的二维码扫描界面网址"""

    def get(self, request):
        next = request.query_params.get('next')
        oauth = QQOauth(state=next)
        login_url = oauth.get_login_url()
        return Response({'login_url': login_url})


#
class QQAuthUserView(GenericAPIView):

    serializer_class = serializer.QQAuthUserSerializer
    def get(self, request):
        code = request.query_params.get('code')
        if code is None:
            return Response({'massage': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        oauth = QQOauth()

        try:
            access_token = oauth.get_access_token(code)
            open_id = oauth.get_openid(access_token)
        except QQAPIException as e:
            logger.error(e)
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            oauth_user = OAuthQQUser.objects.get(openid=open_id)
        except OAuthQQUser.DoesNotExist:
            token = oauth.generate_save_user_token(open_id)
            return Response({'access_token': token})
        else:
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 使用当前的注册用户user生成载荷，该载荷内部会有{"username":"", "user_id":"", "email":""}
            user = oauth_user.user  # OAuthQQUser模型对象取出user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            return Response({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })

    def post(self, request):
        """
        绑定用户到openid
        GenericAPIView
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 使用当前的注册用户user生成载荷，该载荷内部会有{"username":"", "user_id":"", "email":""}
         # OAuthQQUser模型对象取出user
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return Response({
            'token': token,
            'user_id': user.id,
            'username': user.username
        })




