"""One-shot: re-create meta.json with correct UTF-8 then import all sample assets into DB.

Avoids the Windows GBK encoding corruption by writing meta.json inline and
then importing all 20 assets in the same Python process.
"""
import os, sys, json, asyncio, hashlib, uuid, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.db.session import AsyncSessionLocal, init_db
from app.models.asset import Asset
from app.models.user import User
from sqlalchemy import select

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample-assets")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uploads", "assets")

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

async def main():
    await init_db()

    # Get admin user ID
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.role == "admin").limit(1))
        admin = result.scalar_one_or_none()
        admin_id = admin.id if admin else None
        await db.commit()

    if not admin_id:
        print("ERROR: No admin user found! Run generate_test_users.py first.")
        return

    # 1) Write clean meta.json
    meta = [{"name": s["name"], "tags": s["tags"], "desc": s["desc"],
             "type": f"image/{s['name'].rsplit('.',1)[-1]}"} for s in SAMPLES]
    meta_path = os.path.join(SAMPLE_DIR, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("✅ meta.json written with correct UTF-8")

    # Verify meta.json was written correctly
    with open(meta_path, "r", encoding="utf-8") as f:
        verify = json.load(f)
    print(f"   Verify first tag: {verify[0]['tags'][:3]}")

    # 2) Import images
    imported = 0
    skipped = 0
    for s in SAMPLES:
        src = os.path.join(SAMPLE_DIR, s["name"])
        if not os.path.exists(src):
            print(f"  SKIP (no file): {s['name']}")
            skipped += 1
            continue

        content = open(src, "rb").read()
        content_hash = hashlib.sha256(content).hexdigest()
        ext = os.path.splitext(s["name"])[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                    ".gif": "image/gif", ".webp": "image/webp"}
        file_type = mime_map.get(ext, "image/jpeg")

        async with AsyncSessionLocal() as db:
            # Check for existing by original name
            result = await db.execute(
                select(Asset).where(Asset.original_name == s["name"])
            )
            if result.scalar_one_or_none():
                print(f"  SKIP (exists): {s['name']}")
                skipped += 1
                await db.rollback()
                continue

            asset_id = str(uuid.uuid4())
            dest_dir = os.path.join(UPLOAD_DIR, asset_id)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, s["name"])
            with open(dest, "wb") as f:
                f.write(content)

            asset = Asset(
                id=asset_id,
                filename=s["name"],
                original_name=s["name"],
                file_type=file_type,
                file_size=len(content),
                file_path=dest,
                tags=s["tags"],
                ai_tags=s["tags"],
                ai_description=s["desc"],
                status="ready",
                version=1,
                uploaded_by=admin_id,
            )
            db.add(asset)
            await db.flush()
            await db.commit()
            imported += 1
            print(f"  [{imported}] {s['name']}  tags={s['tags'][:3]}")

    print(f"\n✅ Done! Imported {imported} new, skipped {skipped} (duplicates/missing).")

if __name__ == "__main__":
    asyncio.run(main())
