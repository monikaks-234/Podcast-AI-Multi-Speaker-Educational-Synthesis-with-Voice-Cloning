import os

avatars_dir = "web/static/avatars"
if os.path.exists(avatars_dir):
    files = os.listdir(avatars_dir)
    print("Avatar files in web/static/avatars:", files)
else:
    print("Avatar directory does not exist.")
