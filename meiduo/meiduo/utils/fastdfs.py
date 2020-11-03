"""
该模块中需要自定义一个存储后端，来实现获取完整的图片链接
"""

# Django基础存储后端基类(Storage)
from django.core.files.storage import Storage
from django.conf import settings

class FastDFSStorage(Storage):

    def __init__(self, fdfs_base_url=None):
        """
        构造方法，可以不带参数，也可以携带参数
        :param base_url: Storage的IP
        """
        self.fdfs_base_url = fdfs_base_url or settings.FDFS_BASE_URL

    # 打开本地文件(作用于文件上传) —— Django项目二需要使用
    def _open(self, name, mode='rb'):
        pass

    # 保存文件数据(作用于文件上传) —— Django项目二需要使用
    def _save(self, name, content, max_length=None):
        pass

    # 该函数的返回值就是，ImageField字段url属性的结果
    def url(self, name):
        # 功能：返回图片的链接
        # 我们需要重写该函数，构建完整图片链接返回
        # 参数：name指ImageField字段在数据库mysql中存储的值，即是文件的id
        # name = "group1/M00/00/02/CtM3BVrPCAOAIKRBAAGvaeRBMfc0463515"
        # return "http://image.meiduo.site:8888/" + name
        return  self.fdfs_base_url + name