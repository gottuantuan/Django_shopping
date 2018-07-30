from django.contrib import admin
from . import models
# Register your models here.







class SKUAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """
        当站点中点击保存按钮时调用的
        :param request: 本次保存模型数据的请求对象
        :param obj: 本次要保存的SKU模型对象
        :param form: 本次要操作的表单
        :param change: 本次操作时变化的数据
        :return: None
        """
        # 调用父类的保存的操作，后续不用关心存储,只关系触发异步任务
        obj.save()

        # 触发异步任务
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        # sku.id  == obj.id
        generate_static_sku_detail_html.delay(obj.id)


class SKUSpecificationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

    def delete_model(self, request, obj):
        """
        站点删除数据时被调用的
        :param request: 本次保存模型数据的请求对象
        :param obj: 本次要删除的SKU模型对象
        :return: None
        """
        sku_id = obj.sku.id
        obj.delete()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


class SKUImageAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

        # 设置SKU默认图片
        sku = obj.sku
        if not sku.default_image_url:
            sku.default_image_url = obj.image.url
            sku.save()

    def delete_model(self, request, obj):
        sku_id = obj.sku.id
        obj.delete()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


class GoodsCategoryAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        from celery_tasks.html.tasks import generate_static_list_search_html
        generate_static_list_search_html.delay()

    def delete_model(self, request, obj):
        obj.delete()
        from celery_tasks.html.tasks import generate_static_list_search_html
        generate_static_list_search_html.delay()


admin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage)