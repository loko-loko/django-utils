import boto3
from loguru import logger

class S3Client():

    def __init__(self, cfg):
        self._client = self._get_client(**self._build_credentials(cfg))
        self._bucket = cfg["s3"]["bucket"]
        # Create bucket if not exist
        self._create_bucket()

    @staticmethod
    def _build_credentials(cfg):
        return {"access_key": cfg["ssh"]["access_key"],
                "secret_key": cfg["s3"]["secret_key"],
                "s3_url": cfg["s3"]["url"]}

    @staticmethod
    def _get_client(access_key, secret_key, s3_url):
        logger.debug(f"[s3] Init client -> access_key:{access_key}, secret_key:****, s3_url: {s3_url}")
        try:
            client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=s3_url
            )
            return client
        except Exception as e:
            logger.error(f"[s3] Init S3 client errot: {e}")

    @property
    def client(self):
        return self._client

    def _check_bucket(self):
        try:
            logger.debug("[s3] List S3 buckets")
            response = self._client.list_buckets()
            for bucket in response['Buckets']:
                if bucket['Name'] == self._bucket:
                    return True
            return False
        except Exception as e:
            logger.error(f"[s3] Check bucket error: {e}")

    def _create_bucket(self):
        if self._check_bucket:
            logger.info(f"[s3] Bucket {self._bucket} exist. skip")
            return
        logger.info(f"[s3] Creation of bucket {self._bucket}")
        try:
            self._client.create_bucket(Bucket=self._bucket)
        except Exception as e:
            logger.error(f"[s3] Creation bucket error: {e}")

    def upload_file(self, path_file, s3_path_file):
        logger.info(f"[s3] Upload file -> source:{path_file}, dest:s3://{self._bucket}/{s3_path_file}")
        try:
            self._client.upload_file(Bucket=self._bucket,
                                     Filename=path_file,
                                     Key=s3_path_file)
        except Exception as e:
            logger.error(f"Upload file to bucket error: {e}")
        return s3_path_file

    def download_file(self, s3_path_file, path_file):
        logger.info(f"[s3] Download file -> source:s3://{self._bucket}/{s3_path_file}, dest:{path_file}")
        try:
            self._client.download_file(Bucket=self._bucket,
                                       Filename=path_file,
                                       Key=s3_path_file)
        except Exception as e:
            logger.error(f"[s3] Download file from bucket error: {e}")
        return path_file
