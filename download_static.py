import os
import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_static_files():
    """下载必要的静态文件"""
    try:
        # 创建目录
        os.makedirs('static/css', exist_ok=True)
        os.makedirs('static/js', exist_ok=True)
        
        # 文件 URL 映射
        files = {
            'static/js/bootstrap.bundle.min.js': 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js',
            'static/js/bootstrap.bundle.min.js.map': 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js.map',
            'static/js/echarts.min.js': 'https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js',
            'static/css/bootstrap.min.css': 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css',
            'static/css/bootstrap.min.css.map': 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css.map',
            'static/js/jquery.min.js': 'https://cdn.bootcdn.net/ajax/libs/jquery/3.6.0/jquery.min.js'
        }
        
        # 下载文件
        for file_path, url in files.items():
            try:
                if os.path.exists(file_path):
                    logger.info(f'文件已存在，跳过下载: {file_path}')
                    continue
                    
                logger.info(f'正在下载: {url}')
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f'下载成功: {file_path}')
                else:
                    logger.error(f'下载失败: {url}, 状态码: {response.status_code}')
                    
            except Exception as e:
                logger.error(f'下载出错 {url}: {str(e)}')
                
    except Exception as e:
        logger.error(f'下载静态文件失败: {str(e)}')
        raise

if __name__ == '__main__':
    try:
        download_static_files()
        logger.info('所有静态文件下载完成')
    except Exception as e:
        logger.error(f'程序执行失败: {str(e)}') 