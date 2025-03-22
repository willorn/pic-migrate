import requests
from ..base_uploader import BaseUploader
import os
import json
from typing import Optional

class SMSUploader(BaseUploader):
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.upload_url = "https://smms.app/api/v2/upload"
        self.headers = {
            "Authorization": api_token
        }

    def upload_file(self, file_path: str, remote_path: str) -> str:
        """
        上传文件到 SM.MS 图床
        
        Args:
            file_path: 本地文件路径
            remote_path: 远程路径（在 SM.MS 中不需要使用）
            
        Returns:
            str: 上传成功后的图片URL
            
        Raises:
            Exception: 上传失败时抛出异常
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, 'rb') as f:
            files = {'smfile': f}
            response = requests.post(
                self.upload_url,
                headers=self.headers,
                files=files
            )

        if response.status_code != 200:
            raise Exception(f"上传失败，状态码: {response.status_code}")

        result = response.json()
        
        if not result.get('success'):
            error_message = result.get('message', '未知错误')
            raise Exception(f"上传失败: {error_message}")

        return result['data']['url']

    def _handle_response(self, response: requests.Response) -> Optional[str]:
        """
        处理响应数据
        
        Args:
            response: 请求响应对象
            
        Returns:
            Optional[str]: 成功返回URL，失败返回None
        """
        try:
            result = response.json()
            if result['success']:
                return result['data']['url']
            return None
        except json.JSONDecodeError:
            return None