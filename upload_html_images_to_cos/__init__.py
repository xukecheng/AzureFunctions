import logging
import azure.functions as func
import json
from bs4 import BeautifulSoup
import requests
from qcloud_cos import CosConfig, CosS3Client
import os
import datetime
from urllib.parse import urlparse
import re

# 复用现有的 COS 配置
secret_id = os.environ["COS_SECRET_ID"]
secret_key = os.environ["COS_SECRET_KEY"]
region = os.environ["COS_REGION"]
bucket_name = os.environ["COS_BUCKET_NAME"]

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=None, Scheme="https")
client = CosS3Client(config)


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

                # 获取文件扩展名
                file_ext = os.path.splitext(urlparse(src).path)[1].lower() or ".jpg"
                if file_ext.startswith("."):
                    file_ext = file_ext[1:]

                # 如果不是图片格式，跳过
                if file_ext not in ["jpg", "jpeg", "png", "gif", "webp", "bmp"]:
                    logging.warning(f"Unsupported image format: {file_ext} for {src}")
                    continue

                # 生成 object_key，使用与现有函数相同的路径格式
                timestamp = datetime.datetime.now()
                object_key = (
                    f"images/{timestamp.strftime('%Y')}/{timestamp.strftime('%m')}/"
                    f"{timestamp.strftime('%Y%m%d%H%M%S')}_{len(processed_results)}.{file_ext}"
                )

                # 上传到 COS
                client.put_object(Bucket=bucket_name, Body=response.content, Key=object_key, EnableMD5=False)

                # 更新图片 URL
                new_url = f"https://{bucket_name}.cos.{region}.myqcloud.com/{object_key}"
                img["src"] = new_url

                processed_results.append({"old_url": src, "new_url": new_url, "size": len(response.content)})

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
