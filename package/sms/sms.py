import sys

from typing import List

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from init import logger
from alibabacloud_tea_util.client import Client as UtilClient


class SMSClientWrapper:
    def __init__(self, access_key_id: str, access_key_secret: str):
        self.client = self.create_client(access_key_id, access_key_secret)

    def create_client(
        self,
        access_key_id: str,
        access_key_secret: str,
    ) -> Dysmsapi20170525Client:
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = f'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    def send_message(self, phone_number: str, sign_name: str, template_code: str, template_param: str):
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers=phone_number,
            sign_name=sign_name,
            template_code=template_code,
            template_param=template_param
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = self.client.send_sms_with_options(send_sms_request, runtime)
            return None
        except Exception as error:
            logger.error(f'SMSClientWrapper, send_message, phone_number:{phone_number} error:{error}')
            return error

