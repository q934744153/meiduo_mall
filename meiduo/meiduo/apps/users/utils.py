from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from users.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django import http
from django.conf import settings
from meiduo.utils.secret import SecretOauth
class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self,request,username = None,password=None,**kwargs):
        try:
            user = User.objects.get(Q(username=username)|Q(mobile=username))

        except User.DoesNotExist as e:
            return None

        if user.check_password(password):
            return user


class LoginRequiredJSONMixin(LoginRequiredMixin):

    def handle_no_permission(self):
        return http.JsonResponse({'code': 400, 'errmsg': '用户未登录'})

def generate_verify_email_url(request):
    # 1.user_id email
    data_dict = {
        'user_id': request.user.id,
        'email': request.user.email
    }
    # 2.将参数加密
    dumps_data = SecretOauth().dumps(data_dict)

    # 3.拼接 完整的激活路由
    verify_url = settings.EMAIL_VERIFY_URL + dumps_data

    return verify_url

