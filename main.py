from pathlib import Path
import os
from dotenv import load_dotenv
from utils.logger import logger  # 修改这里
from storage.uploaders.sms_uploader import SMSUploader
from markdown.image_downloader import MarkdownImageDownloader

# 加载环境变量
load_dotenv()

def main():
    # 配置路径
    markdown_dir = Path("C:\\Users\\tianyi\\WebstormProjects\\tackle_challenge\\docs")  # 你的markdown文件所在目录
    # markdown_dir = Path("D:\\file_repo\\obsidian")  # 你的markdown文件所在目录
    save_dir = Path("./tests/20250322")  # 图片保存目录
    uploader = SMSUploader(api_token=os.getenv('SMS_API_TOKEN'))

    # 创建下载器实例
    downloader = MarkdownImageDownloader(str(save_dir), uploader)

    # 获取所有md文件
    md_files = list(markdown_dir.glob("**/*.md"))

    if not md_files:
        logger.warning(f"在 {markdown_dir} 目录下没有找到markdown文件")
        return

    logger.info(f"找到 {len(md_files)} 个markdown文件")

    total_success = 0
    total_failed = 0

    # 处理每个文件
    for md_file in md_files:
        logger.info(f"正在处理文件: {md_file}")
        results = downloader.process_markdown_file(str(md_file))

        # 统计结果
        success_count = len(results['success'])
        failed_count = len(results['failed'])
        total_success += success_count
        total_failed += failed_count

        # 输出成功信息
        if success_count > 0:
            logger.info(f"成功下载 {success_count} 张图片:")
            for item in results['success']:
                logger.info(f"  - {item['url']} -> {item['save_path']}")

        # 输出失败信息
        if failed_count > 0:
            logger.warning(f"下载失败 {failed_count} 张图片:")
            for item in results['failed']:
                logger.error(f"  - {item['url']}: {item['error']}")

    # 输出总结
    logger.info("=== 下载完成 ===")
    logger.info(f"总成功: {total_success} 张")
    logger.info(f"总失败: {total_failed} 张")


if __name__ == "__main__":
    main()
