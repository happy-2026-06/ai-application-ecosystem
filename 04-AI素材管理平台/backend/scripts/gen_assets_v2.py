"""v2: Generate sample assets with English filenames + Chinese metadata tags.

Images are rendered with English labels on them (which render reliably on
all platforms), but the metadata tags/descriptions stored in the DB are
Chinese so the DAM demo is authentic.
"""
import os, sys, json, random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample-assets")

# 20 samples — English filenames, Chinese tags + descriptions
SAMPLES = [
    {"name": "sunset_beach_silhouette.jpg",  "tags": ["夕阳", "海滩", "剪影", "暖色调", "风景"],
     "desc": "金色夕阳下海岸线的剪影，橘红色天空与深色海洋形成鲜明对比"},
    {"name": "modern_city_skyline.jpg",       "tags": ["城市", "天际线", "建筑", "夜景", "都市"],
     "desc": "黄昏时分现代城市天际线全景，灯光初亮的摩天大楼群"},
    {"name": "spring_cherry_blossom.jpg",    "tags": ["樱花", "春天", "自然", "粉色", "风景"],
     "desc": "盛开的樱花树，粉白色花瓣在蓝天映衬下格外柔美"},
    {"name": "misty_mountain_morning.jpg",   "tags": ["山", "晨雾", "自然", "绿色", "风景"],
     "desc": "清晨薄雾缭绕的青山，层层叠叠的远山如水墨画般"},
    {"name": "red_sports_car.jpg",           "tags": ["跑车", "红色", "速度", "产品", "金属"],
     "desc": "亮红色豪华跑车侧面特写，金属车身反射着流动的光线"},
    {"name": "fresh_fruit_platter.jpg",      "tags": ["美食", "水果", "彩色", "食物", "健康"],
     "desc": "色彩缤纷的新鲜水果拼盘，草莓橙子蓝莓猕猴桃搭配"},
    {"name": "business_portrait.jpg",        "tags": ["人物", "商务", "肖像", "专业", "人像"],
     "desc": "年轻商务人士的专业肖像照，浅灰背景搭配暖色光线"},
    {"name": "old_european_building.jpg",    "tags": ["建筑", "欧式", "古老", "石头", "历史"],
     "desc": "欧洲古镇的石砌建筑，斑驳墙面记录了百年历史"},
    {"name": "tech_product_showcase.jpg",    "tags": ["产品", "科技", "展示", "白色", "简约"],
     "desc": "白色背景的科技产品简约展示，极简主义构图风格"},
    {"name": "autumn_forest_path.jpg",       "tags": ["秋天", "森林", "小路", "暖色", "自然"],
     "desc": "秋日森林中蜿蜒小路，金黄色的树叶铺满地面"},
    {"name": "blue_ocean_wave.jpg",          "tags": ["海洋", "海浪", "蓝色", "动态", "自然"],
     "desc": "深蓝色海浪冲击礁石的瞬间，白色浪花飞溅"},
    {"name": "aurora_snowy_night.jpg",       "tags": ["极光", "雪景", "绿色", "星空", "自然"],
     "desc": "绿色极光在雪地上空舞动，星空与冰雪交织的奇幻画面"},
    {"name": "coffee_shop_interior.jpg",     "tags": ["室内", "咖啡", "设计", "温暖", "建筑"],
     "desc": "温馨的现代风格咖啡店室内设计，暖黄灯光与木色家具"},
    {"name": "yoga_sunrise_beach.jpg",       "tags": ["瑜伽", "冥想", "人物", "宁静", "健康"],
     "desc": "海边日出的瑜伽冥想场景，人与自然和谐统一"},
    {"name": "handmade_pottery_art.jpg",     "tags": ["手工", "陶艺", "产品", "艺术", "质感"],
     "desc": "手工制作的陶艺作品，泥土质感与釉色光泽完美结合"},
    {"name": "rainy_night_city_street.jpg",  "tags": ["城市", "夜景", "街道", "霓虹", "都市"],
     "desc": "雨夜城市街道，霓虹灯倒映在湿润的柏油路面上"},
    {"name": "summer_sunflower_field.jpg",   "tags": ["向日葵", "花田", "夏天", "黄色", "自然"],
     "desc": "一望无际的向日葵花田，金黄色花海在夏日阳光下绽放"},
    {"name": "cute_cat_closeup.jpg",         "tags": ["宠物", "猫咪", "特写", "可爱", "动物"],
     "desc": "虎斑猫近距离特写，翠绿色眼睛和柔软毛发纹理"},
    {"name": "brand_logo_design.png",        "tags": ["Logo", "设计", "品牌", "极简", "创意"],
     "desc": "现代极简风格品牌Logo设计方案，圆形几何图形组合"},
    {"name": "winter_cabin_snow.jpg",        "tags": ["冬天", "雪景", "小屋", "温暖", "风景"],
     "desc": "冬日森林中亮着灯光的小木屋，烟囱冒青烟温暖宁静"},
]

COLORS = {
    "夕阳": ("#FF6B35", "#F7C948"),
    "城市": ("#2D1B69", "#6366F1"),
    "自然": ("#059669", "#6EE7B7"),
    "建筑": ("#78716C", "#D6D3D1"),
    "美食": ("#DC2626", "#FBBF24"),
    "人物": ("#7C3AED", "#C084FC"),
    "产品": ("#2563EB", "#93C5FD"),
    "海滩": ("#006994", "#48B5E0"),
    "海洋": ("#1E3A8A", "#06B6D4"),
    "冬天": ("#94A3B8", "#F1F5F9"),
    "夜景": ("#0F0B1E", "#3B82F6"),
    "跑车": ("#991B1B", "#F59E0B"),
    "樱花": ("#F472B6", "#FCE7F3"),
    "秋天": ("#B45309", "#FDE68A"),
    "宠物": ("#78350F", "#F59E0B"),
    "极光": ("#064E3B", "#34D399"),
    "室内": ("#92400E", "#FCD34D"),
    "科技": ("#1E40AF", "#60A5FA"),
    "瑜伽": ("#5B21B6", "#A78BFA"),
}

def hex2rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def gen(sample, i):
    W, H = 800, 600
    # Pick a matching color pair
    hex1, hex2 = None, None
    for kw, cols in COLORS.items():
        if any(kw in t for t in sample["tags"]):
            hex1, hex2 = cols; break
    if not hex1: hex1, hex2 = "#6366F1", "#A855F7"
    c1, c2 = hex2rgb(hex1), hex2rgb(hex2)

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Gradient
    for y in range(H):
        r = int(c1[0] + (c2[0]-c1[0]) * y/H)
        g = int(c1[1] + (c2[1]-c1[1]) * y/H)
        b = int(c1[2] + (c2[2]-c1[2]) * y/H)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Decorative circles
    for _ in range(6):
        cx, cy = random.randint(80, W-80), random.randint(80, H-80)
        rr = random.randint(50, 140)
        draw.ellipse([cx-rr,cy-rr,cx+rr,cy+rr], fill=(255,255,255,30), outline=(255,255,255,20), width=2)

    # Dots pattern
    for _ in range(25):
        x,y = random.randint(0,W), random.randint(0,H)
        s = random.randint(2,5)
        draw.rectangle([x,y,x+s,y+s], fill=(255,255,255,35))

    # Label bar at bottom
    draw.rectangle([0, 490, W, H], fill=(0,0,0,55))

    # Text (use default font for reliability)
    try:
        fbig = ImageFont.truetype("C:\\Windows\\Fonts\\Arial.ttf", 32)
        fsm = ImageFont.truetype("C:\\Windows\\Fonts\\Arial.ttf", 18)
    except:
        try:
            fbig = ImageFont.truetype("arial.ttf", 32)
            fsm = ImageFont.truetype("arial.ttf", 18)
        except:
            fbig = ImageFont.load_default()
            fsm = ImageFont.load_default()

    # English label on image
    label = sample["name"].replace("_", " ").rsplit(".",1)[0].title()
    bbox = draw.textbbox((0,0), label, font=fbig)
    tw = bbox[2]-bbox[0]
    draw.text(((W-tw)//2+1, 503), label, font=fbig, fill=(0,0,0,80))
    draw.text(((W-tw)//2, 502), label, font=fbig, fill=(255,255,255,230))

    # Chinese tags subtitle
    tag_str = " · ".join(sample["tags"][:4])
    b2 = draw.textbbox((0,0), tag_str, font=fsm)
    tw2 = b2[2]-b2[0]
    draw.text(((W-tw2)//2+1, 552), tag_str, font=fsm, fill=(0,0,0,60))
    draw.text(((W-tw2)//2, 551), tag_str, font=fsm, fill=(210,210,255,200))

    path = os.path.join(OUTPUT_DIR, sample["name"])
    img.save(path, quality=85)
    return path, os.path.getsize(path)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    meta = []
    print(f"Generating {len(SAMPLES)} images...")
    for i, s in enumerate(SAMPLES):
        path, size = gen(s, i)
        meta.append({"name": s["name"], "tags": s["tags"], "desc": s["desc"],
                      "type": f"image/{s['name'].rsplit('.',1)[-1]}"})
        print(f"  [{i+1:2d}] {s['name']} ({size:,} bytes)  tags={s['tags'][:3]}")

    with open(os.path.join(OUTPUT_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\nDone. Metadata: {os.path.join(OUTPUT_DIR, 'meta.json')}")


if __name__ == "__main__":
    main()
