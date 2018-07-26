from django_redis import get_redis_connection
from redis import RedisError
from rest_framework import serializers

import logging
# 日志记录器
logger = logging.getLogger('django')


class ImageCodeCheckSerializer(serializers.Serializer):
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)


      # 联合校验text,需要用到image_code_id
    # attrs == validated_data
    def validate(self, attrs):
        image_code_id = attrs.get('image_code_id')
        text = attrs.get('text')
        #获取redis中的短信验证码
        redis_conn = get_redis_connection('verify_codes')
        image_code_server = redis_conn.get('img_%s' % image_code_id)
        if image_code_server is None:
            raise serializers.ValidationError('无效的图片验证码')
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)
        image_code_server = image_code_server.decode()
        if text.lower() != image_code_server.lower():
            raise serializers.ValidationError('图片验证码不符')
        mobile = self.context['view'].kwargs['mobile']
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise serializers.ValidationError('发送短信频繁')
        return attrs