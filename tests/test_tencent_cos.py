import os
import pytest
from pathlib import Path
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.tencent_cos import TencentCOSUploader

@pytest.fixture
def cos_uploader():
    """创建 COS 上传器实例"""
    return TencentCOSUploader(
        secret_id=os.getenv('COS_SECRET_ID'),
        secret_key=os.getenv('COS_SECRET_KEY'),
        region=os.getenv('COS_REGION'),
        bucket=f"{os.getenv('COS_BUCKET')}-{os.getenv('COS_APP_ID')}"  # 正确拼接 bucket 名称
    )

@pytest.fixture
def invalid_test_file(tmp_path):
    """创建用于无效凭证测试的临时文件"""
    test_file = tmp_path / "invalid_test.txt"
    test_file.write_text("test content")
    return test_file

def test_upload_with_invalid_credentials(invalid_test_file):
    """测试无效凭证"""
    invalid_uploader = TencentCOSUploader(
        secret_id="invalid",
        secret_key="invalid",
        region="ap-beijing",
        bucket="invalid-bucket-12345678"
    )

    result = invalid_uploader.upload_file(invalid_test_file, "test.txt")
    assert result == False  # 期望返回 False 而不是抛出异常