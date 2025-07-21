from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """Custom storage for static files in S3"""

    location = "static"
    default_acl = "public-read"
    querystring_auth = False
    file_overwrite = True


class MediaStorage(S3Boto3Storage):
    """Custom storage for media files in S3"""

    location = "media"
    default_acl = "public-read"
    file_overwrite = False
    querystring_auth = False
