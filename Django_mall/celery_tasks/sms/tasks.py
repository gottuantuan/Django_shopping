from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks.main import celery_app
from . import constants

@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    # 异步的发送短信
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)

