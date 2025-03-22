# Pic-Migrate

一个用于批量迁移 Markdown 文档中图片到图床的工具。

## 功能特点

- 支持多种图床服务
  - SM.MS 图床
  - 腾讯云 COS
  - 可扩展的上传器接口
- 智能处理图片
  - 自动检测并跳过已迁移的图片
  - 保持原始文件名和时间信息
  - 支持多种图片格式（jpg, png, gif, webp）
- 限速保护
  - 智能控制上传频率
  - 避免触发图床限制
- Markdown 文件处理
  - 支持标准 Markdown 图片语法
  - 支持 HTML 图片标签
  - 自动更新文档中的图片链接

## 安装

```bash
# 克隆项目
git clone https://github.com/your-username/pic-migrate.git

# 安装依赖
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env` 文件：

```plaintext
# 选择上传器类型（cos 或 sms）
UPLOAD_TYPE=sms

# SMS 图床配置
SMS_API_TOKEN=你的_API_TOKEN

# 腾讯云 COS 配置（如果使用 COS）
COS_SECRET_ID=你的_SECRET_ID
COS_SECRET_KEY=你的_SECRET_KEY
COS_REGION=ap-shanghai
COS_BUCKET=你的存储桶名称
```

## 使用方法

```bash
# 运行程序
python main.py
```

默认会处理 `tests` 目录下的所有 Markdown 文件。

## 注意事项

- SM.MS 图床有以下限制：
  - 每分钟最多上传 15 张图片
  - 每小时最多上传 100 张图片
  - 单个文件大小限制为 5MB
- 建议在迁移前备份原始文件
- 确保网络连接稳定

## 开发说明

### 添加新的上传器

1. 在 `storage/uploaders` 目录下创建新的上传器类
2. 继承 `BaseUploader` 基类
3. 实现 `upload_file` 方法

示例：
```python
from ..base_uploader import BaseUploader

class NewUploader(BaseUploader):
    def upload_file(self, file_path: str, remote_path: str) -> str:
        # 实现上传逻辑
        return "图片URL"
```

## License

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request！