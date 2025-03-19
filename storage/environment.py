import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import os

@dataclass
class TencentConfig:
    config_name: str
    version: str
    secret_id: str
    secret_key: str
    area: str
    app_id: str
    bucket: str
    endpoint: str = ""
    path: str = ""
    custom_url: str = ""
    options: str = ""
    slim: bool = False

class StorageConfig:
    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> TencentConfig:
        """加载配置信息"""
        # 首先尝试从环境变量加载
        load_dotenv()
        
        # 如果提供了配置文件，优先使用配置文件
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                tcyun = config.get('tcyun', {})
                return TencentConfig(
                    config_name=tcyun.get('_configName', ''),
                    version=tcyun.get('version', 'v5'),
                    secret_id=tcyun.get('secretId', ''),
                    secret_key=tcyun.get('secretKey', ''),
                    area=tcyun.get('area', ''),
                    app_id=tcyun.get('appId', ''),
                    bucket=tcyun.get('bucket', ''),
                    endpoint=tcyun.get('endpoint', ''),
                    path=tcyun.get('path', ''),
                    custom_url=tcyun.get('customUrl', ''),
                    options=tcyun.get('options', ''),
                    slim=tcyun.get('slim', False)
                )
        
        # 否则使用环境变量
        return TencentConfig(
            config_name=os.getenv('COS_CONFIG_NAME', 'txpic'),
            version=os.getenv('COS_VERSION', 'v5'),
            secret_id=os.getenv('COS_SECRET_ID', ''),
            secret_key=os.getenv('COS_SECRET_KEY', ''),
            area=os.getenv('COS_REGION', 'ap-shanghai'),
            app_id=os.getenv('COS_APP_ID', ''),
            bucket=os.getenv('COS_BUCKET', ''),
            endpoint=os.getenv('COS_ENDPOINT', ''),
            path=os.getenv('COS_PATH', ''),
            custom_url=os.getenv('COS_CUSTOM_URL', ''),
            options=os.getenv('COS_OPTIONS', ''),
            slim=os.getenv('COS_SLIM', 'false').lower() == 'true'
        )