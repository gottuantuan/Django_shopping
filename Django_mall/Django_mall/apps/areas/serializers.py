from rest_framework import serializers

from .models import Area


class AreasSerializer(serializers.ModelSerializer):
    """省级数据序列化器：只做序列化
    list
    """
    class Meta:
        model = Area
        fields = ['id', 'name']


class SubsAreasSerializer(serializers.ModelSerializer):
    """城市或者区县数据序列化器：只做序列化
    retrieve
    """

    # subs关联AreasSerializer
    # 目的：让subs的数据来源于AreasSerializer序列化之后的结果
    subs = AreasSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'name', 'subs']