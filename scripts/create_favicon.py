from PIL import Image, ImageDraw
import os


def create_favicon():
    """创建一个股票K线形状的网站图标"""
    # 创建一个32x32的图像，使用深蓝色背景
    size = 32
    background_color = '#1a365d'
    line_color = '#ffffff'
    
    img = Image.new('RGB', (size, size), background_color)
    draw = ImageDraw.Draw(img)
    
    # 绘制简化的K线图形
    margin = 4
    width = size - 2 * margin
    height = size - 2 * margin
    
    # 绘制上升趋势线
    draw.line([
        (margin, height + margin),  # 起点
        (width + margin, margin)    # 终点
    ], fill=line_color, width=2)
    
    # 绘制K线柱
    bar_width = 3
    positions = [(8, 20), (14, 16), (20, 12), (26, 8)]
    for x, y in positions:
        draw.rectangle([
            (x, y),
            (x + bar_width, y + 6)
        ], fill=line_color)
    
    # 确保目录存在
    os.makedirs('static/images', exist_ok=True)
    
    # 保存为ICO文件
    img.save('static/images/favicon.ico')


if __name__ == '__main__':
    create_favicon() 