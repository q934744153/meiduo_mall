from django.core.mail import send_mail
from meiduo.settings import dev
import logging
from celery_tasks.main import celery_app
logger = logging.getLogger('django')

@celery_app.task(name='send_verify_email')
def send_verify_email(to_email,verify_url):
    subject = "美多商城邮箱验证"
    # 发送内容:
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    print(to_email)
    # 进行发送
    result = send_mail(subject=subject,
                       message="",
                       from_email=dev.EMAIL_FROM,
                       recipient_list=[to_email],
                       html_message=html_message
                       )
    print(verify_url)

    return result