from celery import Celery
#實例化對象
celery_app = Celery('meiduo')
#配置路徑
celery_app.config_from_object('celery_tasks.config')
#任務路徑
celery_app.autodiscover_tasks(['celery_tasks.sms'])

