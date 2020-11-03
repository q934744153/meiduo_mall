from django.shortcuts import render
from django.views import View

from goods.models import *
from contents.models import *

class IndexView(View):

    # 获取完整的index.html页面返回
    # 请求方式：GET
    # 请求路径：/
    def get(self, request):
        # 1、获取动态数据(模版参数)
        # 查询商品频道和分类
        categories = {}
        channels = GoodsChannel.objects.order_by('group_id', 'sequence')
        for channel in channels:
            group_id = channel.group_id  # 当前组

            if group_id not in categories:
                categories[group_id] = {'channels': [], 'sub_cats': []}

            cat1 = channel.category  # 当前频道的类别

            # 追加当前频道
            categories[group_id]['channels'].append({
                'id': cat1.id,
                'name': cat1.name,
                'url': channel.url
            })
            # 构建当前类别的子类别
            for cat2 in cat1.subs.all():
                cat2.sub_cats = []
                for cat3 in cat2.subs.all():
                    cat2.sub_cats.append(cat3)
                categories[group_id]['sub_cats'].append(cat2)

        # 广告数据
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 渲染模板的上下文
        context = {
            'categories': categories,
            #'contents': contents
        }
        # 2、页面渲染返回 —— 把模版参数传入模版中，渲染出完整的html页面
        # render函数功能就是传入模版参数渲染完整页面，并构建成响应对象返回
        # render(请求对象，模版文件，模版参数)
        response = render(request, 'index.html', context=context)
        return response