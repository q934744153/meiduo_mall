
from haystack import indexes
from .models import SKU

# 索引模型类名：{模型类}Index
class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    """SKU索引数据模型类"""
    # 检索字段，该字段中保存了分词，将来根据用户查找的关键词在text保存的分词中匹配查找
    # use_template=True,使用模版来指定分词包含django模型类的哪些被用于搜索的字段
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """返回建立索引的模型类"""
        return SKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据查询集"""
        return self.get_model().objects.filter(is_launched=True)