
from rest_framework import serializers
from goods.models import SKU

class CartSerializer(serializers.Serializer):
    '''序列化器和反序列化器'''
    sku_id = serializers.IntegerField(label='商品SKU ID', min_value=1)
    count = serializers.IntegerField(label='数量', min_value=1)
    selected = serializers.BooleanField(label='是否勾选，默认勾选',default=True)

    def validate(self, data):
        # sku_id = data.get('sku_id')
        # count = data.get('count')
        try:
            sku_id = SKU.objects.get(id=data['sku_id'])
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        if data['count'] > sku_id.stock:
            raise serializers.ValidationError('商品库存不足')

        return data


class CartSKUSerializer(serializers.ModelSerializer):

    '''查询序列化器'''

    count = serializers.IntegerField(label='商品数量')
    selected = serializers.BooleanField(label='是否勾选')


    class Meta():

        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price', 'selected')


class CartDeleteSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(label='商品id', min_value=1)

    def validate_sku_id(self, value):
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value



class CartSelectAllSerializer(serializers.Serializer):
    """
    购物车全选
    """
    selected = serializers.BooleanField(label='全选')



