"""
DATABASE TUZATISH SKRIPTI
Bu skript shop_items jadvalidagi image_url ustunini TEXT ga o'zgartiradi.
Shundan keyin Base64 rasmlar saqlanishi mumkin bo'ladi.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app, db
from sqlalchemy import text

def fix_shop_database():
    with app.app_context():
        print("🔧 Shop Database ni tuzatish boshlandi...\n")
        
        try:
            # Step 1: Check current column type
            result = db.session.execute(text("""
                SELECT data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'shop_items' AND column_name = 'image_url'
            """)).fetchone()
            
            if result:
                print(f"📊 Hozirgi holat: {result[0]}, Max length: {result[1]}")
            
            # Step 2: Alter column to TEXT
            print("\n🔨 image_url ustunini TEXT ga o'zgartirish...")
            db.session.execute(text("ALTER TABLE shop_items ALTER COLUMN image_url TYPE TEXT"))
            db.session.commit()
            print("✅ Muvaffaqiyatli o'zgartirildi!")
            
            # Step 3: Verify
            result = db.session.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'shop_items' AND column_name = 'image_url'
            """)).fetchone()
            
            print(f"\n✅ Yangi holat: {result[0]}")
            print("\n🎉 DATABASE TAYYOR! Endi rasmlar o'chmaydi.")
            print("\n⚠️ MUHIM: Eski rasmlar hali ham buzilgan. Ularni o'chirib, yangidan yuklang!")
            
        except Exception as e:
            print(f"\n❌ Xatolik: {str(e)}")
            db.session.rollback()
            
            # Try adding column if it doesn't exist
            try:
                print("\n🔨 Ustun yo'q bo'lsa, yangisini qo'shish...")
                db.session.execute(text("ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS image_url TEXT"))
                db.session.commit()
                print("✅ Yangi ustun qo'shildi!")
            except Exception as ex:
                print(f"❌ Bu ham ishlamadi: {str(ex)}")

if __name__ == "__main__":
    fix_shop_database()
