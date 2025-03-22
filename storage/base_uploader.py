from abc import ABC, abstractmethod


class BaseUploader(ABC):
    @abstractmethod
    def upload_file(self, file_path: str, remote_path: str) -> str:
        """
        上传文件到远程存储
        
        Args:
            file_path: 本地文件路径
            remote_path: 远程存储路径
            
        Returns:
            str: 文件的访问URL
        """
        pass
