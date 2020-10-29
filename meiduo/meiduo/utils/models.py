from django.db import models

class BaseModel(models.Model):
   create_time = models.DateTimeField(auto_now_add=True,verbose_name='創建時間')
   update_time = models.DateTimeField(auto_now=True,verbose_name='更新時間')

   class Meta:
        abstract = True


