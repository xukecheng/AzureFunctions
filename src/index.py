# -*- coding: utf8 -*-
import json
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging
import requests
import time
import os


# 日志配置
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)

# 环境变量获取
secret_id = os.getenv("SecretId")
secret_key = os.getenv("SecretKey")
region = os.getenv("region")
token = None
scheme = "https"
bucket = os.getenv("Bucket")
cdn_url = os.getenv("CDNURL")


config = CosConfig(
    Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme
)
client = CosS3Client(config)


def main_handler(event, context):
    logger.info("start main handler")

    path_parameters = event["pathParameters"]
    extension_name = path_parameters["extension_name"]
    filename = "%s%s" % (int(round(time.time() * 1000)), f".{extension_name}")

    # 生成上传URL，未限制请求头部和请求参数
    url = client.get_presigned_url(
        Method="PUT",
        Bucket=bucket,
        Key=f"{extension_name}/{filename}",
        Expired=120,  # 120秒后过期，过期时间请根据自身场景定义
    )
    print(url)
    return {
        "isBase64Encoded": false,
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {
            "read_url": f"{cdn_url}/{extension_name}/{filename}",
            "upload_url": url,
        },
    }


if __name__ == "__main__":
    event = event = {
        "body": "",
        "pathParameters": {"extension_name": "png"},
    }
    context = {"request_id": "123"}
    main_handler(event, context)
