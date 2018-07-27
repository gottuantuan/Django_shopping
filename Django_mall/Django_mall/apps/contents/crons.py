
from collections import OrderedDict
from django.conf import settings
from django.template import loader
import os
import time


from goods.models import GoodsChannel
from .models import ContentCategory

def generate_static_index_html():
    '''
    生成静态文件的主页html
    :return: 
    '''
    # 商品频道及分类菜单
    # 使用有序字典保存类别的顺序
    # categories = {
    #     1: { # 组1
    #         'channels': [{'id':, 'name':, 'url':},{}, {}...],
    #         'sub_cats': [{'id':, 'name':, 'sub_cats':[{},{}]}, {}, {}, ..]
    #     },
    #     2: { # 组2
    #
    #     }
    # }
    categories = OrderedDict() #定义可以支持排序的字典一个字典
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')  #查询分组及频道
    for channel in channels:
        group_id = channel.group_id  # 当前组

        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}   #构建好字典内的框架

        cat1 = channel.category  # 当前频道的类别  

        # 追加当前频道
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })
        # 构建当前类别的子类别 
        for cat2 in cat1.goodscategory_set.all():  #将category中的数据填入到表2
            cat2.sub_cats = []
            for cat3 in cat2.goodscategory_set.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]['sub_cats'].append(cat2)

    # 广告内容
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # 渲染模板的上下文
    context = {
        'categories': categories,
        'contents': contents
    }

    # 以下代码：渲染模板

    # 1.通过模板加载器，加载出准备好的'index.html'文件
    # get_template('index.html') ： 会从settings模块的TEMPLATES变量对应的DIRS中读取templates模板文件
    # templates/index.html只是个临时使用的文件夹，当我们生成了静态的主页后，这个模板里面的文件就没有用了
    template = loader.get_template('index.html')
    # 2.将查询并构造好的context，动态的渲染到'index.html'
    # html_text ： 是经过动态渲染好的html字符串 （Content-Type : text/html）
    html_text = template.render(context)
    # print(html_text)

    # 3.将html字符串写入到指定的文件'index.html'
    # settings.GENERATED_STATIC_HTML_FILES_DIR : 指向front_end_pc/   +  'index.html'
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')

    # encoding ： 用于解决在定时器执行时中文字符编码的问题
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)