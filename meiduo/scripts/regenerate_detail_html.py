"""
定义函数，实现sku商品详情静态化页面，部署在静态服务器文件夹front_end_pc目录中
"""
#!/usr/bin/env python
import os,sys
# 把外层meiduo_mall加入导包路径
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# 在一个独立的脚本中手动加载django配置文件导包路径
os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo.settings.dev'
# 手动加载配置文件
import django
django.setup()


#from django.conf import settings
#from django.template import loader
from goods.utils import *


# 生成静态详情页

def generate_static_sku_detail_html(sku):
    """
    功能：生成指定sku商品的静态化页面
    :param sku: sku商品对象
    :return: 无
    """
    #1、构建模版参数
    categories = get_categories()
    breadcrumb = get_breadcrumb(sku.category.id)
    goods, sku, specs = get_goods_and_spec(sku.id)
    # 渲染页面
    context = {
        'categories': categories,  # 渲染分类
        'breadcrumb': breadcrumb,  # 渲染导航
        'goods': goods,  # 商品价格等信息
        'sku': sku,  # 商品价格等信息
        'specs': specs,  # 商品规格信息
    }

    # 2、渲染页面
    # 2.1、获取模版对象
    template = loader.get_template('detail.html')
    # 2.2、传入模版参数，渲染页面得到完整的页面数据
    html = template.render(context=context)
    # 3、把页面数据存储成静态html文件，放入front_end_pc目录下
    prefix = os.path.dirname(os.path.dirname(settings.BASE_DIR))
    file_path = os.path.join(
        prefix,
        'front_end_pc/goods/%s.html' % sku.id  # sku_id:1 --> ~/front_end_pc/goods/1.html
    )
    print('123', prefix)
    with open(file_path, 'w') as f:
        f.write(html)


if __name__ == '__main__':
    # 获取所有sku商品
    skus = SKU.objects.all()
    # 分别静态化
    for sku in skus:
        generate_static_sku_detail_html(sku)