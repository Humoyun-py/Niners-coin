"""
HOMEWORK IMAGE MIGRATION SCRIPT
Converts old file-based homework images to Base64 for permanent storage
"""
import sys
import os
import base64

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, 'backend')

# Add backend to path
sys.path.insert(0, backend_dir)
sys.path.insert(0, script_dir)

# Change to backend directory for imports to work
os.chdir(backend_dir)

from app import app, db
from models.all_models import HomeworkSubmission

def migrate_homework_images():
    with app.app_context():
        print("🔄 Starting homework image migration...\n")
        
        # Get all submissions with image URLs
        submissions = HomeworkSubmission.query.filter(
            HomeworkSubmission.image_url.isnot(None)
        ).all()
        
        print(f"📊 Found {len(submissions)} submissions with images")
        
        converted = 0
        already_base64 = 0
        missing_files = 0
        errors = 0
        
        for sub in submissions:
            try:
                # Skip if already Base64
                if sub.image_url and sub.image_url.startswith('data:'):
                    already_base64 += 1
                    continue
                
                # Try to find the file
                file_path = os.path.join(script_dir, 'frontend', sub.image_url.lstrip('/'))
                
                if not os.path.exists(file_path):
                    print(f"❌ Missing: {sub.image_url} (ID: {sub.id})")
                    missing_files += 1
                    continue
                
                # Read and convert to Base64
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                # Detect image type from extension
                ext = sub.image_url.split('.')[-1].lower()
                mime_type = f"image/{ext}" if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else 'image/jpeg'
                
                # Convert to Base64
                base64_string = base64.b64encode(image_data).decode('utf-8')
                data_url = f"data:{mime_type};base64,{base64_string}"
                
                # Update database
                sub.image_url = data_url
                converted += 1
                
                print(f"✅ Converted: {os.path.basename(file_path)} (ID: {sub.id}, Size: {len(image_data)} bytes)")
                
            except Exception as e:
                print(f"⚠️ Error processing submission {sub.id}: {str(e)}")
                errors += 1
        
        if converted > 0:
            db.session.commit()
            print(f"\n💾 Database updated!")
        
        print("\n" + "="*50)
        print("📈 MIGRATION SUMMARY:")
        print("="*50)
        print(f"✅ Converted to Base64: {converted}")
        print(f"🔵 Already Base64: {already_base64}")
        print(f"❌ Missing files: {missing_files}")
        print(f"⚠️ Errors: {errors}")
        print(f"📊 Total processed: {len(submissions)}")
        print("="*50)
        
        if missing_files > 0:
            print("\n⚠️ IMPORTANT:")
            print("Missing files cannot be recovered - they were deleted when server restarted.")
            print("Students need to re-upload these homework submissions.")

if __name__ == "__main__":
    migrate_homework_images()
