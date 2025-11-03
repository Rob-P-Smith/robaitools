#!/usr/bin/env python3
"""Export URLs of all records with no chunks"""

import sqlite3

DB_PATH = '/home/robiloo/Documents/robaitools/robaidata/crawl4ai_rag.db'
OUTPUT_FILE = '/home/robiloo/Documents/robaitools/nochunks.md'

def main():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    # Find all records with no chunks
    cursor.execute("""
        SELECT c.id, c.url
        FROM crawled_content c
        LEFT JOIN content_chunks ch ON c.id = ch.content_id
        WHERE ch.content_id IS NULL
        ORDER BY c.id DESC
    """)

    records = cursor.fetchall()

    # Write URLs to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(f"# Records with No Chunks\n\n")
        f.write(f"Total: {len(records)}\n\n")
        for record_id, url in records:
            f.write(f"{url}\n")

    print(f"Exported {len(records)} URLs to {OUTPUT_FILE}")

    db.close()

if __name__ == '__main__':
    main()
