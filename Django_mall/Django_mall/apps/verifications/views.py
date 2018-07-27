from django.shortcuts import render
from rest_framework.generics import GenericAPIView

from Django_mall.libs.captcha.captcha import captcha
# Create your views here.
from rest_framework.views import APIView
from django_redis import get_redis_connection
from . import constans
from django.http import HttpResponse
import random
import logging
from celery_tasks.sms.tasks import send_sms_code
from  Django_mall.libs.yuntongxun.sms import CCP
from rest_framework.response import Response
from . import serializers
logger = logging.getLogger('django')




# url('^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
class SMSCodeView(GenericAPIView):
    """
    短信验证码
    传入参数：
        mobile, image_code_id, text
    """
    serializer_class = serializers.ImageCodeCheckSerializer

    def get(self, request, mobile):

        serializers = self.get_serializer(data=request.query_params)
        serializers.is_valid(raise_exception=True)
        #生成验证码
        sms_code = '%06d' %random.randint(0,999999)
        logger.info(sms_code)
        #用云通信发送验证码

        send_sms_code.delay(mobile,sms_code)
        # CCP().send_template_sms(mobile,[sms_code,constans.SMS_CODE_REDIS_EXPIRES//60],1)

        #将验证码保存到redis数据库中
        redis_conn = get_redis_connection('verify_codes')

        #获取短信验证码
        redis_conn.setex('sms_%s' %mobile,constans.SMS_CODE_REDIS_EXPIRES,sms_code)
        #使用管道方法,金调用一次redis库
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' %mobile, constans.SMS_CODE_REDIS_EXPIRES,sms_code)


        #绑定值 使手机号不能频发短信获得验证码,数值周期为60s
        pl.setex('send_flag_%s' % mobile, constans.SEND_SMS_CODE_INTERVAL, 1)
        # redis_conn.setex()
        pl.execute()


        return Response({'message':'ok'})





class ImageCodeView(APIView):
    """
    图片验证码
    """
    def get(self,request, image_code_id):
        '''
        提供图形验证码
        :param request:
        :return:
        '''

        # 生成图片验证码
        text, image = captcha.generate_captcha()
        logger.info(text)

        # 将生成的图片验证码保存到redis数据库中
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.set('img_%s' %image_code_id, text, constans.IMAGE_CODE_REDIS_EXPIRES)

        # 将图片验证码发送给前段
        return HttpResponse(image, content_type="images/jpg")
