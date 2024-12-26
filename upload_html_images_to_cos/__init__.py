import logging
import azure.functions as func
import json
from bs4 import BeautifulSoup
import requests
from qcloud_cos import CosConfig, CosS3Client
import os
import datetime
import hashlib
from urllib.parse import urlparse
from qcloud_cos.cos_exception import CosServiceError


# 复用现有的 COS 配置
secret_id = os.environ["COS_SECRET_ID"]
secret_key = os.environ["COS_SECRET_KEY"]
region = os.environ["COS_REGION"]
bucket_name = os.environ["COS_BUCKET_NAME"]

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=None, Scheme="https")
client = CosS3Client(config)


def get_file_md5(content):
    """计算文件内容的 MD5 值"""
    return hashlib.md5(content).hexdigest()


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    try:
        # 获取请求体内容
        req_body = req.get_json()
        html_content = req_body.get("html")
        title = req_body.get("title")
        url = req_body.get("url")

        if not html_content:
            return func.HttpResponse(
                json.dumps({"code": 400, "msg": "Missing HTML content in request body", "data": None}),
                mimetype="application/json",
                status_code=400,
            )

        # 解析 HTML
        soup = BeautifulSoup(html_content, "html.parser")
        processed_results = []

        # 处理所有图片
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src or not src.startswith("http"):
                continue

            try:
                # 下载图片
                response = requests.get(src, stream=True)
                if response.status_code != 200:
                    logging.warning(f"Failed to download image from {src}: Status code {response.status_code}")
                    continue

                # 获取文件内容和 MD5
                content = response.content
                file_md5 = get_file_md5(content)

                # 获取文件扩展名
                file_ext = os.path.splitext(urlparse(src).path)[1].lower() or ".jpg"
                if file_ext.startswith("."):
                    file_ext = file_ext[1:]

                if file_ext not in ["jpg", "jpeg", "png", "gif", "webp", "bmp"]:
                    logging.warning(f"Unsupported image format: {file_ext} for {src}")
                    continue

                # 使用 MD5 作为文件名的一部分
                timestamp = datetime.datetime.now()
                object_key = (
                    f"html_images/{timestamp.strftime('%Y')}/{timestamp.strftime('%m')}/" f"{file_md5}.{file_ext}"
                )

                # 检查文件是否已存在
                file_exists = client.object_exists(Bucket=bucket_name, Key=object_key)

                if not file_exists:
                    # 文件不存在，上传到 COS
                    client.put_object(Bucket=bucket_name, Body=content, Key=object_key, EnableMD5=False)
                    logging.info(f"Uploaded new file: {object_key}")
                else:
                    logging.info(f"File already exists: {object_key}")

                # 更新图片 URL
                new_url = f"https://{bucket_name}.cos.{region}.myqcloud.com/{object_key}"
                img["src"] = new_url

                processed_results.append(
                    {
                        "old_url": src,
                        "new_url": new_url,
                        "size": len(content),
                        "md5": file_md5,
                        "is_new": not file_exists,
                    }
                )

                logging.info(f"Successfully processed image: {src} -> {new_url}")

            except Exception as e:
                logging.error(f"Failed to process image {src}: {str(e)}")
                continue

        # 返回处理结果
        return func.HttpResponse(
            json.dumps(
                {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "title": title,
                        "url": url,
                        "html": str(soup),
                        "processed_images": processed_results,
                        "total_processed": len(processed_results),
                    },
                }
            ),
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Function failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({"code": 500, "msg": f"Internal server error: {str(e)}", "data": None}),
            mimetype="application/json",
            status_code=500,
        )
