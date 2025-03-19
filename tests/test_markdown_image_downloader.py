import pytest
from pathlib import Path
from markdown.image_downloader import MarkdownImageDownloader

@pytest.fixture
def downloader(tmp_path):
    return MarkdownImageDownloader(str(tmp_path / "images"))

@pytest.fixture
def sample_md_file(tmp_path):
    content = """
# Test Markdown
![测试图片1](https://example.com/image1.jpg)
Some text here
<img src="https://example.com/image2.png" alt="测试图片2" />
More text
![测试图片3](https://example.com/image3.gif)
    """
    md_file = tmp_path / "test.md"
    md_file.write_text(content, encoding='utf-8')
    return str(md_file)

def test_extract_images(downloader):
    content = """
    ![测试](https://example.com/1.jpg)
    <img src="https://example.com/2.png" />
    """
    urls = downloader.extract_images(content)
    assert len(urls) == 2
    assert urls[0] == "https://example.com/1.jpg"
    assert urls[1] == "https://example.com/2.png"

def test_process_markdown_file(downloader, sample_md_file, requests_mock):
    # Mock请求响应
    requests_mock.get('https://example.com/image1.jpg', content=b'fake-image-1')
    requests_mock.get('https://example.com/image2.png', content=b'fake-image-2')
    requests_mock.get('https://example.com/image3.gif', content=b'fake-image-3')
    
    # Mock HEAD请求
    requests_mock.head('https://example.com/image1.jpg', headers={'Content-Type': 'image/jpeg'})
    requests_mock.head('https://example.com/image2.png', headers={'Content-Type': 'image/png'})
    requests_mock.head('https://example.com/image3.gif', headers={'Content-Type': 'image/gif'})
    
    results = downloader.process_markdown_file(sample_md_file)
    
    assert len(results['success']) == 3
    assert len(results['failed']) == 0