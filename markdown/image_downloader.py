import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urlparse, unquote

import requests

from storage.tencent_cos import TencentCOSUploader  # 添加这行到文件顶部的导入部分


class MarkdownImageDownloader:
    def __init__(self, save_dir: str, cos_uploader: TencentCOSUploader = None):
        """
        初始化下载器
        :param save_dir: 图片保存目录
        :param cos_uploader: COS上传器实例
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.cos_uploader = cos_uploader

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
            if success and self.cos_uploader:
                try:
                    # 生成新的对象名称（使用原始文件名）
                    object_name = f"images/{Path(save_path).name}"

                    # 上传到COS
                    upload_success = self.cos_uploader.upload_file(save_path, object_name)

                    if upload_success:
                        # 获取新的URL
                        new_url = f"https://{self.cos_uploader.bucket}.cos.{self.cos_uploader.region}.myqcloud.com/{object_name}"
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
                    results["failed"].append({
                        "url": url,
                        "error": f"上传出错: {str(e)}"
                    })
            elif not success:
                results["failed"].append({
                    "url": url,
                    "error": error
                })

        # 如果有成功上传的图片，更新Markdown文件
        if url_mapping and self.cos_uploader:
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
        return [url.strip() for url in urls if url.strip()]

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
