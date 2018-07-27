from django.db import models

from Django_mall.utils.models import BaseModel
# Create your models here.


class OAuthQQUser(BaseModel):
    """
    QQ登录用户数据
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='美多商城用户')
    openid = models.CharField(max_length=64, verbose_name='QQ服务器的openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name






