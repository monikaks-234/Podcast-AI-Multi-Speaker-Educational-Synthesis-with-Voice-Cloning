import shutil, os

generated_img = r"C:\Users\hp\.gemini\antigravity\brain\676bea9d-df71-4adf-9a82-eed852252045\guest_male_portrait_1786429323480.jpg"
target_guest_male = r"d:\AI PodCast\web\static\avatars\guest_male.jpg"

if os.path.exists(generated_img):
    shutil.copy(generated_img, target_guest_male)
    print(f"Copied {generated_img} to {target_guest_male}")
else:
    print("Generated image file not found.")
