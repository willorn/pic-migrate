import os
import uuid  # 添加 uuid 导入
import pytest
from pathlib import Path
from dotenv import load_dotenv
from storage.tencent_cos import TencentCOSUploader

# 加载环境变量
load_dotenv()

@pytest.fixture
def cos_uploader():
    """创建 COS 上传器实例"""
    bucket = os.getenv('COS_BUCKET')
    app_id = os.getenv('COS_APP_ID')
    
    # 确保 bucket 名称格式正确
    if not bucket.endswith(f"-{app_id}"):
        bucket = f"{bucket}-{app_id}"
        
    return TencentCOSUploader(
        secret_id=os.getenv('COS_SECRET_ID'),
        secret_key=os.getenv('COS_SECRET_KEY'),
        region=os.getenv('COS_REGION'),
        bucket=bucket
    )

@pytest.fixture
def test_image(tmp_path):
    """创建测试图片文件"""
    from PIL import Image
    import numpy as np
    
    # 创建一个简单的测试图片
    image_path = tmp_path / "test_image.png"
    array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    image = Image.fromarray(array)
    image.save(image_path)
    return image_path

def test_upload_image_success(cos_uploader, test_image):
    """测试图片上传成功"""
    # 生成唯一的对象名称
    import uuid
    object_name = f"test_images/{uuid.uuid4()}.png"
    
    # 上传文件
    result = cos_uploader.upload_file(test_image, object_name)
    assert result == True
    
    # 验证文件是否存在
    assert cos_uploader.file_exists(object_name) == True
    
    # 清理测试文件
    try:
        cos_uploader.client.delete_object(
            Bucket=cos_uploader.bucket,
            Key=object_name
        )
    except Exception as e:
        print(f"清理测试文件失败: {e}")

def test_batch_upload_success(cos_uploader, tmp_path):
    """测试批量上传成功"""
    # 创建目标文件夹
    test_folder = f"test_batch_{uuid.uuid4()}"
    
    # 创建多个测试文件
    test_files = []
    test_dir = tmp_path / test_folder
    test_dir.mkdir(exist_ok=True)
    
    for i in range(3):
        file_path = test_dir / f"test_file_{i}.txt"
        file_path.write_text(f"Test content {i}")
        test_files.append(file_path)

    # 批量上传
    results = cos_uploader.batch_upload(test_files, base_dir=test_dir)
    
    # 验证结果
    assert len(results['success']) == len(test_files)
    assert len(results['failed']) == 0
    
    # 验证所有文件都已上传
    for file_path in test_files:
        object_name = file_path.name  # 现在文件会在正确的文件夹下
        assert cos_uploader.file_exists(object_name) == True
    
    # 清理测试文件
    for file_path in test_files:
        try:
            # cos_uploader.client.delete_object(
            #     Bucket=cos_uploader.bucket,
            #     Key=file_path.name
            # )
            print(f"尝试: {e}")
        except Exception as e:
            print(f"清理测试文件失败: {e}")