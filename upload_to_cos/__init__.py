import logging

import azure.functions as func
import json
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import os
import datetime

secret_id = os.environ["COS_SECRET_ID"]
secret_key = os.environ["COS_SECRET_KEY"]
region = os.environ["COS_REGION"]
bucket_name = os.environ["COS_BUCKET_NAME"]

token = None
scheme = "https"

config = CosConfig(
    Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme
)
client = CosS3Client(config)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    object_key = req.params.get("object_key")
    if object_key is None:
        return func.HttpResponse(
            "Please pass a object_key on the query string",
            status_code=400,
        )

    suffix = object_key.split(".")[-1]
    if suffix in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
        object_key = (
            f"images/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    elif suffix in [
        "mp4",
        "avi",
        "mov",
        "flv",
        "wmv",
        "mkv",
        "rmvb",
        "rm",
        "3gp",
        "f4v",
    ]:
        object_key = (
            f"videos/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    elif suffix in ["mp3", "wav", "wma", "ogg", "ape", "flac", "aac", "m4a"]:
        object_key = (
            f"audios/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    elif suffix in [
        "doc",
        "docs",
        "xlxs",
        "xls",
        "csv",
        "pdf",
        "txt",
        "ppt",
        "pptx",
        "docx",
        ".md",
    ]:
        object_key = (
            f"docs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成代码文件上传链接
    elif suffix in ["py", "js", "java", "c", "cpp", "go", "php", "html", "css", "sh"]:
        object_key = (
            f"codes/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成压缩文件上传链接
    elif suffix in ["zip", "rar", "7z", "tar", "gz", "bz2"]:
        object_key = (
            f"archives/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成配置文件上传链接
    elif suffix in ["json", "yml", "yaml", "xml", "ini", "conf"]:
        object_key = (
            f"configs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成字体文件上传链接
    elif suffix in ["ttf", "otf", "woff", "woff2"]:
        object_key = (
            f"fonts/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成数据库文件上传链接
    elif suffix in ["sql", "db", "dbf", "mdb", "pdb", "sqlitedb"]:
        object_key = (
            f"databases/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成可执行文件上传链接
    elif suffix in ["exe", "msi", "apk", "ipa", "dmg"]:
        object_key = (
            f"executables/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成电子书文件上传链接
    elif suffix in ["epub", "mobi", "azw", "azw3", "azw4", "kf8", "kf7"]:
        object_key = (
            f"ebooks/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )
    # 生成其他文件上传链接
    else:
        object_key = (
            f"others/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/"
            + object_key
        )

    # 生成上传 URL，未限制请求头部和请求参数
    presigned_url = client.get_presigned_url(
        Method="PUT",
        Bucket=bucket_name,
        Key=object_key,
        SignHost=False,
        Expired=120,  # 120秒后过期，过期时间请根据自身场景定义
    )
    print(presigned_url)

    if presigned_url:
        return func.HttpResponse(
            json.dumps(
                {
                    "code": 200,
                    "data": {
                        "presigned_url": presigned_url,
                        "view_url": f"https://{bucket_name}.cos.{region}.myqcloud.com/{object_key}",
                    },
                    "msg": "success",
                }
            )
        )
    else:
        return func.HttpResponse(
            "Please pass a name on the query string or in the request body",
            status_code=400,
        )
