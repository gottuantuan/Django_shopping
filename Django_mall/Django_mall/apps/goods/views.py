from django.shortcuts import render
from rest_framework.generics import ListAPIView
from .models import SKU
from .serializers import SKUSerializer,SKUIndexSerializer
from rest_framework.filters import OrderingFilter
# Create your views here.
from drf_haystack.viewsets import HaystackViewSet

class SKUListView(ListAPIView):
    #指定查询级

    # queryset = SKU.objects.all()

    #指定序列话器

    serializer_class = SKUSerializer

    #排序
    filter_backends = [OrderingFilter]

    # ordering_fields ： 内部需要填写模型的属性，告诉DRF的排序将来对这几个字段排序
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id= category_id, is_launched=True)



class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索的后端
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer

