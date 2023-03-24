import os
from storages.backends.s3boto3 import S3Boto3Storage

AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")


class MediaStorage(S3Boto3Storage):
    bucket_name = AWS_STORAGE_BUCKET_NAME
    location = "media"


class StaticStorage(S3Boto3Storage):
    bucket_name = AWS_STORAGE_BUCKET_NAME
    location = "static"
