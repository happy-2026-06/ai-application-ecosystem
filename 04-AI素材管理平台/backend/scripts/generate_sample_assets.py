"""Generate sample asset images for the DAM platform demo.

Creates placeholder images with labels, gradients, and varied content types:
- Landscapes (sunset, beach, city, nature)
- Products (electronics, fashion, food)
- People (portrait, team)
- Architecture (building, interior)

Run: python scripts/generate_sample_assets.py
Output: sample-assets/ directory with 20 images
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample-assets")

# Define 24 sample assets with Chinese tags
SAMPLES = [
    # Landscapes (images)
    {"name": "夕阳海滩剪影.jpg", "type": "image", "tags": ["夕阳", "海滩", "剪影", "暖色调", "风景"], "desc": "金色夕阳下海岸线的剪影，橘红色天空与深色海洋形成鲜明对比"},
    {"name": "现代城市天际线.jpg", "type": "image", "tags": ["城市", "天际线", "建筑", "夜景", "都市"], "desc": "黄昏时分现代城市天际线全景，灯光初亮的摩天大楼群"},
    {"name": "樱花树下的春天.jpg", "type": "image", "tags": ["樱花", "春天", "自然", "粉色", "风景"], "desc": "盛开的樱花树，粉白色花瓣在蓝天映衬下格外柔美"},
    {"name": "山间晨雾风景.jpg", "type": "image", "tags": ["山", "晨雾", "自然", "绿色", "风景"], "desc": "清晨薄雾缭绕的青山，层层叠叠的远山如水墨画般"},
    {"name": "红色跑车特写.jpg", "type": "image", "tags": ["跑车", "红色", "速度", "产品", "金属"], "desc": "亮红色豪华跑车侧面特写，金属车身反射着流动的光线"},
    {"name": "新鲜水果拼盘.jpg", "type": "image", "tags": ["美食", "水果", "彩色", "食物", "健康"], "desc": "色彩缤纷的新鲜水果拼盘，草莓橙子蓝莓猕猴桃搭配"},
    {"name": "商务人物肖像.jpg", "type": "image", "tags": ["人物", "商务", "肖像", "专业", "人像"], "desc": "年轻商务人士的专业肖像照，浅灰色背景搭配暖色光线"},
    {"name": "古老欧式建筑.jpg", "type": "image", "tags": ["建筑", "欧式", "古老", "石头", "历史"], "desc": "欧洲古镇的石砌建筑，斑驳的墙面记录了百年历史"},
    {"name": "科技产品展示.jpg", "type": "image", "tags": ["产品", "科技", "展示", "白色", "简约"], "desc": "白色背景的科技产品简约展示，极简主义构图风格"},
    {"name": "秋日森林小路.jpg", "type": "image", "tags": ["秋天", "森林", "小路", "暖色", "自然"], "desc": "秋日森林中蜿蜒的小路，两旁金黄色的树叶铺满地面"},
    {"name": "蓝色海浪冲击.jpg", "type": "image", "tags": ["海洋", "海浪", "蓝色", "动态", "自然"], "desc": "深蓝色海浪冲击礁石的瞬间，白色浪花飞溅充满力量感"},
    {"name": "极光下的雪景.jpg", "type": "image", "tags": ["极光", "雪景", "绿色", "星空", "自然"], "desc": "绿色极光在雪地上空舞动，星空与冰雪交织的奇幻画面"},
    {"name": "咖啡店室内设计.jpg", "type": "image", "tags": ["室内", "咖啡", "设计", "温暖", "建筑"], "desc": "温馨的现代风格咖啡店室内设计，暖黄灯光与木色家具"},
    {"name": "瑜伽冥想场景.jpg", "type": "image", "tags": ["瑜伽", "冥想", "人物", "宁静", "健康"], "desc": "海边日出的瑜伽冥想场景，人与自然和谐统一的画面"},
    {"name": "手工陶艺作品.jpg", "type": "image", "tags": ["手工", "陶艺", "产品", "艺术", "质感"], "desc": "手工制作的陶艺作品，泥土质感与釉色光泽的完美结合"},
    {"name": "夜间城市街道.jpg", "type": "image", "tags": ["城市", "夜景", "街道", "霓虹", "都市"], "desc": "雨夜城市街道，霓虹灯倒映在湿润的柏油路面上"},
    {"name": "夏日向日葵花田.jpg", "type": "image", "tags": ["向日葵", "花田", "夏天", "黄色", "自然"], "desc": "一望无际的向日葵花田，金黄色花海在夏日阳光下灿烂绽放"},
    {"name": "宠物猫咪特写.jpg", "type": "image", "tags": ["宠物", "猫咪", "特写", "可爱", "动物"], "desc": "虎斑猫的近距离特写，翠绿色的眼睛和柔软的毛发纹理"},
    {"name": "品牌Logo设计.png", "type": "image", "tags": ["Logo", "设计", "品牌", "极简", "创意"], "desc": "现代极简风格品牌Logo设计方案，圆形几何图形组合"},
    {"name": "冬季雪景小屋.jpg", "type": "image", "tags": ["冬天", "雪景", "小屋", "温暖", "风景"], "desc": "冬日森林中亮着灯光的小木屋，烟囱冒着青烟，温暖宁静"},
]


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_image(index: int, sample: dict) -> str:
    """Generate a 800x600 placeholder image with a gradient and label."""
    W, H = 800, 600
    img = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(img)

    # Pick a color scheme based on tags
    color_schemes = {
        "夕阳": ("#FF6B35", "#F7C948"),
        "海滩": ("#006994", "#48B5E0"),
        "城市": ("#2D1B69", "#6366F1"),
        "自然": ("#059669", "#6EE7B7"),
        "建筑": ("#78716C", "#D6D3D1"),
        "美食": ("#DC2626", "#FBBF24"),
        "人物": ("#7C3AED", "#C084FC"),
        "产品": ("#2563EB", "#93C5FD"),
        "夜景": ("#0F0B1E", "#3B82F6"),
        "跑车": ("#991B1B", "#F59E0B"),
        "海洋": ("#1E3A8A", "#06B6D4"),
        "冬天": ("#94A3B8", "#F1F5F9"),
        "猫咪": ("#78350F", "#F59E0B"),
        "樱花": ("#F472B6", "#FCE7F3"),
    }

    first_tag = sample["tags"][0]
    # Find matching color scheme
    colors = None
    for key, val in color_schemes.items():
        if any(key in tag for tag in sample["tags"]):
            colors = val
            break
    if not colors:
        colors = ("#6366F1", "#A855F7")  # default indigo gradient

    c1 = hex_to_rgb(colors[0])
    c2 = hex_to_rgb(colors[1])

    # Draw gradient background
    for y in range(H):
        ratio = y / H
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Add some decorative shapes
    for _ in range(5):
        x = random.randint(50, W - 50)
        y = random.randint(50, H - 50)
        r = random.randint(40, 120)
        alpha = random.randint(15, 40)
        shape_color = (255, 255, 255, alpha)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=shape_color, outline=shape_color)

    # Draw a subtle pattern overlay
    for _ in range(20):
        x = random.randint(0, W)
        y = random.randint(0, H)
        size = random.randint(2, 6)
        draw.rectangle([x, y, x + size, y + size], fill=(255, 255, 255, 30))

    # Draw the label
    label = sample["name"]
    tags_str = " · ".join(sample["tags"][:3])

    # Try to get a font, fall back to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Semi-transparent label background
    label_bg_h = 100
    label_bg_top = H - label_bg_h
    draw.rectangle([0, label_bg_top, W, H], fill=(0, 0, 0, 60))

    # Center text
    bbox = draw.textbbox((0, 0), label, font=font_large)
    tw = bbox[2] - bbox[0]
    tbx = (W - tw) // 2
    draw.text((tbx + 2, label_bg_top + 18), label, font=font_large, fill=(0, 0, 0, 80))
    draw.text((tbx, label_bg_top + 16), label, font=font_large, fill=(255, 255, 255, 240))

    bbox2 = draw.textbbox((0, 0), tags_str, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    tbx2 = (W - tw2) // 2
    draw.text((tbx2 + 1, label_bg_top + 60), tags_str, font=font_small, fill=(0, 0, 0, 60))
    draw.text((tbx2, label_bg_top + 59), tags_str, font=font_small, fill=(200, 200, 255, 200))

    # Save
    filepath = os.path.join(OUTPUT_DIR, sample["name"])
    img.convert("RGB").save(filepath, quality=85)
    return filepath


def generate_metadata_json():
    """Generate a metadata JSON for the import script."""
    data = []
    for i, s in enumerate(SAMPLES):
        data.append({
            "index": i,
            "name": s["name"],
            "file_type": f"image/{s['name'].split('.')[-1].lower()}",
            "tags": s["tags"],
            "ai_tags": s["tags"],
            "ai_description": s["desc"],
        })
    meta_path = os.path.join(OUTPUT_DIR, "sample-metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return meta_path


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating {len(SAMPLES)} sample images to: {OUTPUT_DIR}")
    for i, sample in enumerate(SAMPLES):
        path = generate_image(i, sample)
        print(f"  [{i+1}/{len(SAMPLES)}] {sample['name']} ({os.path.getsize(path)} bytes)")
    meta_path = generate_metadata_json()
    print(f"\nMetadata: {meta_path}")
    print("Done! Run the import script to load them into the app.")


if __name__ == "__main__":
    main()
