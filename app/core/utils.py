import sys
import os
import boto3
import time
import logging
import threading
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import time as dt_time
from typing import BinaryIO
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.core.constants import GUEST_COOKIE_NAME, MAX_RETRIES, RETRY_DELAY_SECONDS


def convert_to_time(value) -> dt_time:
    """Convert a timedelta (e.g., from DB TIME columns) to a Python time object."""
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return dt_time(hour=hours, minute=minutes, second=seconds)


def running_in_pytest() -> bool:
    return "pytest" in sys.modules


def _guest_cookie_key_func(request: Request):
    return request.cookies.get(GUEST_COOKIE_NAME) or get_remote_address(request)


limiter = Limiter(
    key_func=_guest_cookie_key_func,
    default_limits=[] if running_in_pytest() else ["10/2 second"],
)


def _send(to, msg):
    for _ in range(MAX_RETRIES):
        try:
            with SMTP(os.getenv("EMAIL_HOST", "smtp.gmail.com"), int(os.getenv("EMAIL_PORT", 587))) as smtp:
                smtp.starttls()
                smtp.login(os.getenv("EMAIL_USERNAME", ""), os.getenv("EMAIL_PASSWORD", ""))
                smtp.sendmail(os.getenv("EMAIL_USERNAME", ""), to, msg.as_string())
                break
        except Exception as ex:
            logging.error(f"Error sending email: {ex}")
            time.sleep(RETRY_DELAY_SECONDS)


def send_email(to: str, subject: str, body: str, wait_until_sent: bool = True):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_FROM_NAME", "System")
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))
    if wait_until_sent:
        _send(to, msg)
    else:
        threading.Thread(
            target=_send,
            args=(to, msg),
        ).start()


def upload_file(file: BinaryIO, file_name: str) -> str:
    "Upload a file and return its link"
    region_name = os.getenv("AWS_REGION_NAME", "eu-central-1")
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        region_name=region_name,
    )
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "")
    s3.upload_fileobj(file, bucket_name, file_name)
    file_url_prefix = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/"
    return file_url_prefix + file_name


def delete_file(file_name: str):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION_NAME"),
    )
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    s3.delete_object(Bucket=bucket_name, Key=file_name)


def get_file_extension(file_name: str) -> str:
    return file_name.split(".")[-1].lower()


def round_to_nearest_hundred(value: int | float):
    return int(round(value / 100.0) * 100)
