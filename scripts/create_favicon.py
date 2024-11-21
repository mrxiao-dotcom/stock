from PIL import Image, ImageDraw
import os

def create_favicon():
    # 创建一个 32x32 的图像
    size = 32
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # 绘制一个简单的图标 - 蓝色方块
    margin = 2
    draw.rectangle([margin, margin, size-margin, size-margin], 
                  fill='#0d6efd', outline='#0a58ca')
    
    # 确保目录存在
    os.makedirs('static/images', exist_ok=True)
    
    # 保存为 ICO 文件
    img.save('static/images/favicon.ico')

if __name__ == '__main__':
    create_favicon() 