import os
import subprocess
from datetime import datetime

# Configuration
PLEX_DB_PATH = "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"  # Chemin de la base de données Plex
PLEX_SQLITE_BIN = "/usr/lib/plexmediaserver/Plex SQLite"  # Chemin du binaire Plex SQLite
LIBRARY_TITLE = "Films"  # Titre de la bibliothèque à traiter

# Récupère l'ID de la bibliothèque à partir de son titre
def get_library_id(conn, library_title):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM library_sections WHERE name = ?",
            (library_title,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            print(f"Bibliothèque '{library_title}' non trouvée.")
            return None
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération de l'ID de la bibliothèque : {e}")
        return None

# Récupère toutes les entrées multimédias à partir de la bibliothèque
def get_all_media(conn, library_section_id):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.title, p.file, m.added_at
            FROM metadata_items m
            JOIN media_items mi ON mi.metadata_item_id = m.id
            JOIN media_parts p ON p.media_item_id = mi.id
            WHERE m.library_section_id = ?
            """,
            (library_section_id,)
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des métadonnées : {e}")
        return []

# Met à jour la date d'ajout en utilisant le binaire Plex SQLite
def update_added_at_with_plex_sqlite(media_id, new_timestamp):
    try:
        update_query = f"UPDATE metadata_items SET added_at = {new_timestamp} WHERE id = {media_id};"
        print(f"Log: Mise à jour prévue pour l'ID {media_id} avec la date {new_timestamp}")
        subprocess.run([PLEX_SQLITE_BIN, PLEX_DB_PATH, update_query], check=True)
        print(f"Updated media ID {media_id} to {new_timestamp}")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la mise à jour avec le binaire Plex SQLite : {e}")

# Main
if __name__ == "__main__":
    import sqlite3

    # Connexion initiale pour récupérer les métadonnées
    conn = None
    try:
        conn = sqlite3.connect(PLEX_DB_PATH)
        print("Connexion à la base de données réussie.")

        # Récupérer l'ID de la bibliothèque
        library_id = get_library_id(conn, LIBRARY_TITLE)
        if library_id:
            # Récupérer toutes les entrées multimédias
            media_files = get_all_media(conn, library_id)
            if media_files:
                for media in media_files:
                    media_id, title, file_path, added_at = media
                    print(f"Média récupéré : ID={media_id}, Titre='{title}', Chemin='{file_path}', Date actuelle={added_at}")

                    # Vérifier que le fichier existe
                    if os.path.exists(file_path):
                        mod_time = os.path.getmtime(file_path)
                        update_added_at_with_plex_sqlite(media_id, int(mod_time))
                    else:
                        print(f"Fichier introuvable : {title} ({file_path})")
            else:
                print("Aucune entrée multimédia trouvée dans la bibliothèque.")
        else:
            print("Impossible de trouver l'ID de la bibliothèque.")
    finally:
        if conn:
            conn.close()
            print("Connexion à la base de données fermée.")
