import storage

#storage.disable_usb_drive()
# import storage
# import os
# 
# # Chemins des fichiers de contrôle
# cache_enabled_file = ".cache-enabled"
# caching_file = ".caching"
# 
# try:
#     # Vérifie si le fichier .cache-enabled existe
#     if cache_enabled_file in os.listdir("/"):
#         try:
#             # Monter le système de fichiers en lecture/écriture
#             storage.remount("/", readonly=False)
#             print("File system mounted as read/write.")
# 
#             # Essayer de créer le fichier .caching
#             with open(caching_file, "w") as f:
#                 f.write("Caching is active.")
#             print(f"{caching_file} created successfully.")
# 
#         except OSError as e:
#             print(f"Error during file operations: {e}")
#     else:
#         # Monter le système de fichiers en lecture seule (par défaut)
#         storage.remount("/", readonly=True)
#         print("File system mounted as read-only.")
# except OSError as e:
#     # En cas d'erreur lors de la vérification du fichier .cache-enabled
#     print(f"Error checking {cache_enabled_file}: {e}")
#     storage.remount("/", readonly=True)
#     print("File system mounted as read-only due to error.")

