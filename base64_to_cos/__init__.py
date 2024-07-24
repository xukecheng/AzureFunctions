import logging
import base64
import azure.functions as func
import os
import json
import uuid
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos.cos_exception import CosServiceError, CosClientError

secret_id = os.environ["COS_SECRET_ID"]
secret_key = os.environ["COS_SECRET_KEY"]
region = os.environ["COS_REGION"]
bucket = os.environ["COS_BUCKET_NAME"]

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
client = CosS3Client(config)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    try:
        # 获取请求中的 Base64 编码图像数据
        base64_data = req.get_json().get("image")
        if not base64_data:
            return func.HttpResponse(
                "Please pass a base64 encoded image in the request body",
                status_code=400,
            )

        # 解码 Base64 数据
        image_data = base64.b64decode(base64_data)

        # 上传图像到 COS
        key = f"xmind/zapier_{str(uuid.uuid4())}.png"  # 可以根据需要生成唯一的名称

        response = client.put_object(
            Bucket=bucket,
            Body=image_data,
            Key=key,
            StorageClass="STANDARD",
            ContentType="image/png",
        )

        # 获取 COS URL
        cos_url = f"https://{bucket}.cos.{region}.myqcloud.com/{key}"

        return func.HttpResponse(
            json.dumps(
                {
                    "code": 200,
                    "data": {
                        "url": cos_url,
                    },
                    "msg": "success",
                }
            )
        )
    except (CosServiceError, CosClientError) as e:
        logging.error(f"Error uploading image: {e}")
        return func.HttpResponse("Error uploading image", status_code=500)
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse("Error processing request", status_code=500)
