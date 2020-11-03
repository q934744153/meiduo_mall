from django.conf import settings
from django.template import loader
from .utils import get_categories
from contents.models import ContentCategory
import time
import os
def generate_static_index_html():
    print('%s:generate_static_index_html' % time.ctime())

    categories = get_categories()

    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    context = {
        'categories': categories,
        'contents': contents
    }

    # 获取首页模板文件
    template = loader.get_template('index.html')
    # 渲染首页html字符串
    html = template.render(context)
    # 将首页html字符串写入到指定目录，命名'index.html'
    file_path = os.path.join(os.path.dirname(os.path.dirname(settings.BASE_DIR)), 'front_end_pc/index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)