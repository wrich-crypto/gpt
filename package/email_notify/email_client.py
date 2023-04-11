# -*- coding: utf-8 -*-

import sys
from typing import List
from alibabacloud_dm20151123.client import Client as Dm20151123Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dm20151123 import models as dm_20151123_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class EmailClient:
    def __init__(self, access_key_id: str, access_key_secret: str):
        self.client = self.create_client(access_key_id, access_key_secret)

    def create_client(self, access_key_id: str, access_key_secret: str) -> Dm20151123Client:
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = f'dm.aliyuncs.com'
        return Dm20151123Client(config)

    def send_email(self, single_send_mail_request: dm_20151123_models.SingleSendMailRequest):
        runtime = util_models.RuntimeOptions()
        try:
            self.client.single_send_mail_with_options(single_send_mail_request, runtime)
            return None
        except Exception as error:
            return error

    async def send_email_async(self, single_send_mail_request: dm_20151123_models.SingleSendMailRequest):
        runtime = util_models.RuntimeOptions()
        try:
            await self.client.single_send_mail_with_options_async(single_send_mail_request, runtime)
            return None
        except Exception as error:
            return error


