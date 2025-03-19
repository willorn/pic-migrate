import os
import re
import requests
import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse
import oss2  # 假设使用阿里云OSS
from concurrent.futures import ThreadPoolExecutor

class MDImageProcessor:
    def __init__(self, md_folder, image_folder):
        self.md_folder = Path(md_folder)
        self.image_folder = Path(image_folder)
        self.image_folder.mkdir(parents=True, exist_ok=True)
        
    def get_md_files(self):
        """获取所有MD文件"""
        return list(self.md_folder.glob('**/*.md'))
    
    def extract_image_urls(self, md_file):
        """提取MD文件中的图片链接"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # 匹配图片链接，包括行内图片和引用图片
        pattern = r'!\[.*?\]\((.*?)\)|!\[.*?\]\[.*?\]|(?<=\[.*?\]:\s)(http[s]?://.*?(?:png|jpg|jpeg|gif))'
        urls = re.findall(pattern, content)
        return [url for url in urls if url]
    
    def get_safe_filename(self, url):
        """生成安全的文件名"""
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path))
        # 使用URL的MD5作为文件名，保留原始扩展名
        name_hash = hashlib.md5(url.encode()).hexdigest()
        ext = os.path.splitext(filename)[1]
        return f"{name_hash}{ext}"
    
    def download_image(self, url):
        """下载单个图片"""
        try:
            filename = self.get_safe_filename(url)
            save_path = self.image_folder / filename
            
            if save_path.exists():
                return True, save_path
                
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True, save_path
            return False, None
        except Exception as e:
            print(f"下载失败: {url}, 错误: {str(e)}")
            return False, None
    
    def verify_image(self, image_path):
        """验证图片是否完整"""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    def upload_to_oss(self, local_file, bucket):
        """上传文件到OSS"""
        try:
            object_name = local_file.relative_to(self.image_folder)
            bucket.put_object_from_file(str(object_name), str(local_file))
            return True
        except Exception as e:
            print(f"上传失败: {local_file}, 错误: {str(e)}")
            return False
    
    def process(self):
        """处理所有文件"""
        md_files = self.get_md_files()
        all_images = set()
        
        # 收集所有图片URL
        for md_file in md_files:
            urls = self.extract_image_urls(md_file)
            all_images.update(urls)
        
        # 并行下载图片
        downloaded_files = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.download_image, url): url for url in all_images}
            for future in futures:
                success, file_path = future.result()
                if success and file_path:
                    downloaded_files.append(file_path)
        
        # 验证所有下载的图片
        valid_files = []
        for file_path in downloaded_files:
            if self.verify_image(file_path):
                valid_files.append(file_path)
            else:
                print(f"图片验证失败: {file_path}")
                
        return valid_files