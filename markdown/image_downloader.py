import os
import re
import time
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urlparse, unquote

import requests

from storage.base_uploader import BaseUploader


class MarkdownImageDownloader:
    def __init__(self, save_dir: str, uploader: BaseUploader = None):
        """
        初始化下载器
        :param save_dir: 图片保存目录
        :param uploader: 上传器实例
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.uploader = uploader

        # 分钟级限制
        self.last_upload_time = time.time()
        self.upload_count = 0
        self.upload_limit = 15  # 每分钟最大上传数
        self.upload_interval = 60  # 重置计数器的时间间隔（秒）

        # 小时级限制
        self.hourly_last_reset = time.time()
        self.hourly_upload_count = 0
        self.hourly_upload_limit = 100  # 每小时最大上传数
        self.hourly_interval = 3600  # 一小时的秒数

    def _check_upload_rate(self):
        """检查并控制上传速率"""
        current_time = time.time()

        # 检查小时级限制
        if current_time - self.hourly_last_reset >= self.hourly_interval:
            self.hourly_upload_count = 0
            self.hourly_last_reset = current_time
        elif self.hourly_upload_count >= self.hourly_upload_limit:
            sleep_time = self.hourly_interval - (current_time - self.hourly_last_reset)
            print(f"已达到每小时上传限制，等待 {sleep_time / 60:.1f} 分钟后继续...")
            time.sleep(sleep_time)
            self.hourly_upload_count = 0
            self.hourly_last_reset = time.time()
            current_time = time.time()  # 更新当前时间

        # 检查分钟级限制
        if current_time - self.last_upload_time >= self.upload_interval:
            self.upload_count = 0
            self.last_upload_time = current_time
        elif self.upload_count >= self.upload_limit:
            sleep_time = self.upload_interval - (current_time - self.last_upload_time)
            time.sleep(sleep_time)
            self.upload_count = 0
            self.last_upload_time = time.time()

    def replace_image_urls(self, content: str, url_mapping: Dict[str, str]) -> str:
        """
        替换Markdown内容中的图片URL
        :param content: 原始Markdown内容
        :param url_mapping: 原始URL到新URL的映射
        :return: 更新后的Markdown内容
        """
        for old_url, new_url in url_mapping.items():
            # 替换Markdown格式的图片链接
            content = content.replace(f']({old_url})', f']({new_url})')
            # 替换HTML格式的图片链接
            content = content.replace(f'src="{old_url}"', f'src="{new_url}"')
            content = content.replace(f"src='{old_url}'", f"src='{new_url}'")
        return content

    def process_markdown_file(self, md_file: str) -> Dict[str, List[Dict]]:
        """
        处理单个Markdown文件
        :return: 处理结果统计
        """
        md_path = Path(md_file)
        if not md_path.exists():
            return {
                "success": [],
                "failed": [{"url": "", "error": f"文件不存在: {md_file}"}]
            }

        # 读取Markdown文件
        content = md_path.read_text(encoding='utf-8')

        # 提取图片URL
        image_urls = self.extract_images(content)

        results = {
            "success": [],
            "failed": []
        }

        # 用于存储URL映射关系
        url_mapping = {}

        # 下载并上传每个图片
        for url in image_urls:
            success, error, save_path = self.download_image(url)
            if success and self.uploader:
                try:
                    self._check_upload_rate()

                    object_name = f"images/{Path(save_path).name}"
                    new_url = self.uploader.upload_file(save_path, object_name)

                    if new_url:
                        self.upload_count += 1
                        self.hourly_upload_count += 1
                        url_mapping[url] = new_url
                        results["success"].append({
                            "url": url,
                            "save_path": save_path,
                            "new_url": new_url
                        })
                    else:
                        results["failed"].append({
                            "url": url,
                            "error": "上传失败"
                        })
                except Exception as e:
                    error_str = str(e)
                    # 检查是否是图片已存在的错误
                    if "Image upload repeated limit, this image exists at:" in error_str:
                        # 提取已存在的图片URL
                        existing_url = error_str.split("exists at: ")[-1].strip()
                        # 使用已存在的URL进行替换
                        url_mapping[url] = existing_url
                        results["success"].append({
                            "url": url,
                            "save_path": save_path,
                            "new_url": existing_url,
                            "note": "使用已存在的图片URL"
                        })
                    else:
                        results["failed"].append({
                            "url": url,
                            "error": error_str
                        })
            elif not success:
                results["failed"].append({
                    "url": url,
                    "error": error
                })

        # 如果有成功上传的图片，更新Markdown文件
        if url_mapping and self.uploader:
            try:
                # 替换内容中的URL
                new_content = self.replace_image_urls(content, url_mapping)
                # 写回文件
                md_path.write_text(new_content, encoding='utf-8')
            except Exception as e:
                results["failed"].append({
                    "url": "",
                    "error": f"更新Markdown文件失败: {str(e)}"
                })

        return results

    def extract_images(self, md_content: str) -> List[str]:
        """
        从Markdown内容中提取所有图片URL
        支持以下格式：
        ![alt](url)
        <img src="url" />
        """
        # Markdown标准图片语法
        md_pattern = r'!\[.*?\]\((.*?)\)'
        # HTML图片标签语法
        html_pattern = r'<img.*?src=["\'](.*?)["\'].*?>'

        urls = []
        urls.extend(re.findall(md_pattern, md_content))
        urls.extend(re.findall(html_pattern, md_content))

        # 过滤掉已经在 SM.MS 的图片
        filtered_urls = [
            url.strip() for url in urls
            if url.strip() and 's2.loli.net' not in url.strip()
        ]
        return filtered_urls

    def download_image(self, url: str) -> Tuple[bool, str, str]:
        """
        下载单个图片
        :return: (是否成功, 错误信息, 保存路径)
        """
        try:
            # 解析URL，获取文件名
            parsed_url = urlparse(unquote(url))
            original_filename = os.path.basename(parsed_url.path)

            # 如果URL中没有文件扩展名，尝试从Content-Type获取
            if not os.path.splitext(original_filename)[1]:
                response = requests.head(url)
                content_type = response.headers.get('Content-Type', '')
                ext = self._get_extension_from_content_type(content_type)
                original_filename = f"image{ext}"

            # 下载图片
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 获取最后修改时间
            last_modified = response.headers.get('Last-Modified')
            if last_modified:
                from email.utils import parsedate_to_datetime
                try:
                    date_str = parsedate_to_datetime(last_modified).strftime('%Y%m%d')
                    name, ext = os.path.splitext(original_filename)
                    original_filename = f"{date_str}_{name}{ext}"
                except:
                    pass

            # 保存图片
            save_path = self.save_dir / original_filename
            # 如果文件已存在，添加数字后缀
            counter = 1
            while save_path.exists():
                name, ext = os.path.splitext(original_filename)
                save_path = self.save_dir / f"{name}_{counter}{ext}"
                counter += 1

            with open(save_path, 'wb') as f:
                f.write(response.content)

            return True, "", str(save_path)

        except Exception as e:
            return False, str(e), ""

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """根据Content-Type获取文件扩展名"""
        content_type = content_type.lower()
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'webp' in content_type:
            return '.webp'
        else:
            return '.jpg'  # 默认使用jpg
