from celery import Celery
import os
#實例化對象
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    # 如果没有该环境变量
    # os.environ = {'DJANGO_SETTINGS_MODULE': 'meiduo_mall.settings.dev'}
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo.settings.dev'

celery_app = Celery()
#配置路徑
celery_app.config_from_object('celery_tasks.config')
#任務路徑
celery_app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])

