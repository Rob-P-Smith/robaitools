#!/usr/bin/env python3
"""
Insert Bash Command Categories into RAG Database

This script reads bash.json and inserts each category as a separate database entry
for RAG retrieval. Each category includes all its commands with full details.
"""

import json
import sys
from pathlib import Path

# Add robaimodeltools to path
sys.path.insert(0, str(Path(__file__).parent / 'robaimodeltools'))

from robaimodeltools.data.storage import RAGDatabase


def load_bash_json(filepath='bash.json'):
    """Load and parse bash.json file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def group_commands_by_category(bash_data):
    """Group commands by their category."""
    categories = {}

    for command in bash_data['commands']:
        category = command['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(command)

    return categories


def create_markdown_for_category(category_name, commands):
    """Create markdown content with full JSON of all commands in category."""
    # Create a nice title
    title = category_name.replace('-', ' ').title()

    # Build the category JSON object
    category_data = {
        "category": category_name,
        "command_count": len(commands),
        "commands": commands
    }

    # Format as markdown with JSON code block
    markdown = f"""# {title} Commands

This category contains {len(commands)} command(s) for {category_name.replace('-', ' ')}.

```json
{json.dumps(category_data, indent=2, ensure_ascii=False)}
```
"""

    return markdown


def create_tags_for_category(category_name, commands):
    """Create comma-separated tags: category + all command names."""
    command_names = [cmd['command'] for cmd in commands]
    tags = [category_name] + command_names
    return ', '.join(tags)


def insert_categories_to_database(db_path='robaidata/crawl4ai_rag.db'):
    """Main function to insert all bash categories into the database."""
    print(f"Loading bash.json...")
    bash_data = load_bash_json()

    print(f"Grouping {bash_data['metadata']['total_commands']} commands by category...")
    categories = group_commands_by_category(bash_data)

    print(f"Found {len(categories)} categories: {', '.join(sorted(categories.keys()))}")

    # Initialize database
    print(f"\nConnecting to database: {db_path}")
    db = RAGDatabase(db_path=db_path)

    # Insert each category
    successful = 0
    failed = 0

    for category_name in sorted(categories.keys()):
        commands = categories[category_name]

        try:
            # Create data for this category
            url = f"http://bashcommands.com/{category_name}"
            title = f"{category_name.replace('-', ' ').title()} Commands"
            tags = create_tags_for_category(category_name, commands)
            markdown = create_markdown_for_category(category_name, commands)
            content = ""  # Empty as requested

            # Create metadata
            metadata = {
                "category": category_name,
                "command_count": len(commands),
                "source": "bash.json",
                "type": "bash_reference"
            }

            print(f"\n[{successful + 1}/{len(categories)}] Inserting: {category_name}")
            print(f"  - Commands: {len(commands)}")
            print(f"  - Tags: {tags[:100]}{'...' if len(tags) > 100 else ''}")
            print(f"  - URL: {url}")

            # Store in database (this will generate embeddings)
            db.store_content(
                url=url,
                title=title,
                content=content,
                markdown=markdown,
                retention_policy='permanent',
                tags=tags,
                metadata=metadata
            )

            successful += 1
            print(f"  ✓ Successfully inserted!")

        except Exception as e:
            failed += 1
            print(f"  ✗ Failed to insert {category_name}: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"Insertion complete!")
    print(f"  Successful: {successful}/{len(categories)}")
    print(f"  Failed: {failed}/{len(categories)}")
    print(f"{'='*60}")

    # Verify insertions
    print(f"\nVerifying insertions...")
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        for category_name in sorted(categories.keys()):
            url = f"http://bashcommands.com/{category_name}"
            cursor.execute("SELECT id, title FROM crawled_content WHERE url = ?", (url,))
            result = cursor.fetchone()
            if result:
                print(f"  ✓ {category_name}: Found in database (ID: {result[0]}, Title: {result[1]})")
            else:
                print(f"  ✗ {category_name}: NOT found in database")
        cursor.close()

    db.close()
    print(f"\nDatabase connection closed.")


if __name__ == '__main__':
    print("="*60)
    print("Bash Categories Database Insertion Script")
    print("="*60)

    try:
        insert_categories_to_database()
        print("\n✓ Script completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Script failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
