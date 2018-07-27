from django.conf import settings
from urllib.parse import urlencode,parse_qs
from urllib.request import urlopen
import json
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadData
from . import constants

import logging
logger = logging.getLogger('django')


from .exceptions import QQAPIException


class QQOauth(object):
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        self.client_id = client_id or settings.QQ_CLIENT_ID
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE

    def get_login_url(self):
        """获取login_url
    # login_url = https://graph.qq.com/oauth2.0/authorize?
    response_type=code&client_id=101474184
    &redirect_uri=xx&state=next参数&scope=get_user_info
    """

        url = 'https://graph.qq.com/oauth2.0/authorize?'

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'get_user_info'
        }
        query_params = urlencode(params)
        login_url = url + query_params
        return login_url

    def get_access_token(self, code):
        """
        使用code获取access_token
        :param code: authorization code
        :return: access_toekn
        """
        url = 'https://graph.qq.com/oauth2.0/token?'



        # grant_type 	必须 	授权类型，在本步骤中，此值为“authorization_code”。
        # client_id 	必须 	申请QQ登录成功后，分配给网站的appid。
        # client_secret 	必须 	申请QQ登录成功后，分配给网站的appkey。
        # code 	必须 	上一步返回的authorization code。如果用户成功登录并授权，则会跳转到指定的回调地址，并在URL中带上Authorization Code。
        #                 例如，回调地址为www.qq.com/my.php，则跳转到：
        #                 http://www.qq.com/my.php?code=520DD95263C1CFEA087******
        #                 注意此code会在10分钟内过期。
        # redirect_uri 	必须 	与上面一步中传入的redirect_uri保持一致。

        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        url += urlencode(params)
        try:
            # response_data = (bytes)'access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14'
            response_data = urlopen(url).read()
            response_str = response_data.decode()
            # 尽量的将response_str，转成字典，方便读取access_token
            response_dict = parse_qs(response_str)

            access_token = response_dict.get('access_token')[0]
        except Exception as e:
            logger.error(e)
            raise QQAPIException('获取access_token失败')
        return access_token


    def get_openid(self,access_token):
        """
                使用access_token获取openid
                :param access_token: 获取openid的凭据
                :return: openid
                """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=%s' % access_token
        #callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );
        response_str = ''
        try:
            response_data = urlopen(url).read()
            response_str = response_data.decode()
            # 使用字符串的切片，将response_str中的json字符串切出来
            # 返回的数据 callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            response_dict = json.loads(response_str[10:-4])
            openid = response_dict.get('openid')
        except Exception as e:
            err_data = parse_qs(response_str)
            logger.error(e)
            raise QQAPIException('code=%s msg=%s' % (err_data.get('code'), err_data.get('msg')))
        return openid

    @staticmethod
    def generate_save_user_token(openid):
        """
                生成保存用户数据的token
                :param openid: 用户的openid
                :return: token
                """
        serializer = Serializer(settings.SECRET_KEY,expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        data ={
            'openid': openid
        }

        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_save_user_token(token):
        """
        检验保存用户数据的token
        :param token: token
        :return: openid or None
        """
        serializer = Serializer(settings.SECRET_KEY,expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            return data.get('openid')



