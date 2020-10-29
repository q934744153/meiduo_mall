from django.db import models

# Create your models here.

class Area(models.Model):
    """
    行政区划
    """
    # 创建 name 字段, 用户保存名称
    name = models.CharField(max_length=20, verbose_name='名称')
    # 自关联字段 parent
    # on_delete=models.SET_NULL ---> 当主表数据删除，与之关联的多个从表数据的外间字段设置为NULL
    # null=True  -->  允许设置为空(虚空、虚无，对应Python语言中定义的None)
    # blank=True -->  允许设置为空(空白字符，不可见字符， 如字符串： "  ")
    # related_name='subs' --> 在主表模型类中设置关联隐藏字段，用来记录关联的从表的多条数据
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True, verbose_name='上级行政区划')

    #objects = models.Manager    # 隐藏字段
    # subs = <当前主表对象，关联的多个从表对象>
    class Meta:
        db_table = 'tb_areas'

    def __str__(self):
        return self.name