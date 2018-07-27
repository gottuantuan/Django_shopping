
from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin   #缓存

from .models import Area
from . import serializers


# Create your views here.


class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """省市区三级联动数据
    list:
    获取省级数据

    retrieve:
    获取城市和区县数据
    """

    # 禁用列表数据的分页
    pagination_class = None

    # 指定查询集
    # queryset = Area.objects.all()
    def get_queryset(self):
        if self.action == 'list':
            # 省级数据
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    # 指定序列化器
    def get_serializer_class(self):
        if self.action == 'list':
            # 省级数据
            return serializers.AreasSerializer
        else:
            return serializers.SubsAreasSerializer


