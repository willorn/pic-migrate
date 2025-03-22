import os
from pathlib import Path
from typing import Optional, Dict  # 添加这行导入
from qcloud_cos import CosConfig, CosS3Client, CosServiceError
from .environment import StorageConfig, TencentConfig

class TencentCOSUploader:
    @classmethod
    def from_config(cls, config_path: Optional[Path] = None):
        """从配置文件创建上传器实例"""
        config = StorageConfig.load_config(config_path)
        return cls(
            secret_id=config.secret_id,
            secret_key=config.secret_key,
            region=config.area,
            bucket=f"{config.bucket}-{config.app_id}"  # 确保 bucket 名称包含 appid
        )

    def __init__(self, secret_id: str, secret_key: str, region: str, bucket: str):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region  # 确保这行存在
        self.bucket = bucket
        
        self.client = CosS3Client(
            CosConfig(
                Region=region,
                SecretId=secret_id,
                SecretKey=secret_key
            )
        )

    def upload_file(self, local_file: Path, object_name: str) -> bool:
        """
        上传单个文件到 COS
        
        Args:
            local_file (Path): 本地文件路径
            object_name (str): 对象存储中的文件名
            
        Returns:
            bool: 上传是否成功
        """
        try:
            self.client.upload_file(
                Bucket=self.bucket,
                LocalFilePath=str(local_file),
                Key=object_name
            )
            return True
        except Exception as e:
            print(f"上传失败: {local_file}, 错误: {str(e)}")
            return False

    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否已存在于 COS
        
        Args:
            object_name (str): 对象存储中的文件名
            
        Returns:
            bool: 文件是否存在
        """
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=object_name
            )
            return True
        except CosServiceError as e:
            if e.get_status_code() == 404:
                return False
            raise e

    def batch_upload(self, file_list: list, base_dir: Path = None) -> dict:
        """
        批量上传文件
        
        Args:
            file_list (list): 本地文件路径列表
            base_dir (Path, optional): 基础目录，用于构建对象名称
            
        Returns:
            dict: 上传结果统计
        """
        results = {
            'success': [],
            'failed': []
        }
        
        for local_file in file_list:
            local_file = Path(local_file)
            if base_dir:
                object_name = str(local_file.relative_to(base_dir))
            else:
                object_name = local_file.name
                
            if self.upload_file(local_file, object_name):
                results['success'].append(local_file)
            else:
                results['failed'].append(local_file)
                
        return results