import os
import requests
from pathlib import Path

# 要下载的文件列表
FILES_TO_DOWNLOAD = {
    'css': {
        'bootstrap.min.css': 'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.1.3/css/bootstrap.min.css',
        'bootstrap.min.css.map': 'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.1.3/css/bootstrap.min.css.map',
        'all.min.css': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/all.min.css'
    },
    'js': {
        'bootstrap.bundle.min.js': 'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.1.3/js/bootstrap.bundle.min.js',
        'bootstrap.bundle.min.js.map': 'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.1.3/js/bootstrap.bundle.min.js.map',
        'echarts.min.js': 'https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js'
    },
    'webfonts': {
        'fa-solid-900.woff2': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/webfonts/fa-solid-900.woff2',
        'fa-solid-900.woff': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/webfonts/fa-solid-900.woff',
        'fa-solid-900.ttf': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/webfonts/fa-solid-900.ttf',
        'fa-regular-400.woff2': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/webfonts/fa-regular-400.woff2',
        'fa-regular-400.woff': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/webfonts/fa-regular-400.woff',
        'fa-regular-400.ttf': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/webfonts/fa-regular-400.ttf'
    }
}

def download_file(url, filepath):
    """下载文件到指定路径"""
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 确保目录存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"成功下载: {filepath}")
        
    except Exception as e:
        print(f"下载失败 {url}: {str(e)}")

def main():
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent
    static_dir = root_dir / 'static'
    
    # 下载 CSS 文件
    for filename, url in FILES_TO_DOWNLOAD['css'].items():
        filepath = static_dir / 'css' / 'vendor' / filename
        download_file(url, filepath)
    
    # 下载 JS 文件
    for filename, url in FILES_TO_DOWNLOAD['js'].items():
        filepath = static_dir / 'js' / 'vendor' / filename
        download_file(url, filepath)
    
    # 下载字体文件
    for filename, url in FILES_TO_DOWNLOAD['webfonts'].items():
        filepath = static_dir / 'css' / 'webfonts' / filename
        download_file(url, filepath)

if __name__ == '__main__':
    main() 