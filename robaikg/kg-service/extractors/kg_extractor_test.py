"""
Test script for KG Extractor - DIRECT vLLM TEST for unified entity and relationship extraction
Tests the LLM's ability to extract both entities and relationships in a single pass
Logs the raw response to results.md for analysis
NO GLiNER DEPENDENCY
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.vllm_client import get_vllm_client
from config import settings
from kg_extractor import KGExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test data: Load real markdown from database export
# URL: https://www.geeksforgeeks.org/nlp/perplexity-for-llm-evaluation/
TEST_MARKDOWN_FILE = Path(__file__).parent / "test_markdown.md"

# Load the test markdown
try:
    with open(TEST_MARKDOWN_FILE, 'r', encoding='utf-8') as f:
        TEST_TEXT = f.read()
    logger.info(f"Loaded test markdown from {TEST_MARKDOWN_FILE} ({len(TEST_TEXT)} chars)")
except FileNotFoundError:
    logger.error(f"Test markdown file not found: {TEST_MARKDOWN_FILE}")
    logger.error("Please run: sqlite3 crawl4ai_rag.db \"SELECT markdown FROM crawled_content WHERE url='...' LIMIT 1;\" > test_markdown.md")
    TEST_TEXT = "Error: test_markdown.md not found"
except Exception as e:
    logger.error(f"Error loading test markdown: {e}")
    TEST_TEXT = f"Error: {e}"


async def test_kg_extraction():
    """Test unified knowledge graph extraction and log results"""

    logger.info("=" * 80)
    logger.info("Starting KG Extractor Test (Unified Entity + Relationship Extraction)")
    logger.info("=" * 80)

    # Initialize extractor
    extractor = KGExtractor()

    # Get vLLM client
    logger.info("Initializing vLLM client...")
    vllm_client = await get_vllm_client()

    # Wait for model to be available
    logger.info("Waiting for vLLM model to be available...")
    if not await vllm_client.wait_for_model(max_wait_time=60):
        logger.error("vLLM model not available, exiting")
        return

    logger.info(f"vLLM model ready: {vllm_client.model_name}")

    # Build the prompt
    logger.info("Building KG extraction prompt...")
    prompt = extractor._build_extraction_prompt(TEST_TEXT)
    logger.info(f"Prompt built, length: {len(prompt)} characters")

    # Call vLLM
    logger.info("Calling vLLM for unified KG extraction...")
    logger.info(f"Settings - Max tokens: 131072, Temperature: {settings.VLLM_TEMPERATURE}")

    try:
        response = await vllm_client.complete(
            prompt=prompt,
            max_tokens=131072,  # Very large for comprehensive extraction
            temperature=settings.VLLM_TEMPERATURE,
            repetition_penalty=1.1
        )

        logger.info(f"Response received, length: {len(response)} characters")

        # Parse the response
        logger.info("Parsing LLM response...")
        entities, relationships = extractor._parse_llm_response(response, TEST_TEXT)
        logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships")

        # Write results to file
        results_path = Path(__file__).parent / "results.md"
        logger.info(f"Writing results to {results_path}")

        with open(results_path, "w") as f:
            f.write(f"# KG Extractor Test Results\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Model:** {vllm_client.model_name}\n\n")
            f.write(f"**Test Type:** Unified Entity and Relationship Extraction (Single LLM Call)\n\n")
            f.write(f"---\n\n")

            f.write(f"## Test Configuration\n\n")
            f.write(f"- **Text length:** {len(TEST_TEXT)} characters\n")
            f.write(f"- **Max tokens:** 131072 (very large for comprehensive extraction)\n")
            f.write(f"- **Temperature:** {settings.VLLM_TEMPERATURE}\n")
            f.write(f"- **Timeout:** {settings.VLLM_TIMEOUT} seconds\n")
            f.write(f"- **Min confidence:** {settings.RELATION_MIN_CONFIDENCE}\n\n")

            f.write(f"---\n\n")

            f.write(f"## Test Text\n\n")
            f.write(f"```\n{TEST_TEXT}\n```\n\n")

            f.write(f"---\n\n")

            f.write(f"## Prompt Sent to LLM\n\n")
            f.write(f"```\n{prompt}\n```\n\n")

            f.write(f"---\n\n")

            f.write(f"## Raw LLM Response\n\n")
            f.write(f"**Response length:** {len(response)} characters\n\n")
            f.write(f"```\n{response}\n```\n\n")

            f.write(f"---\n\n")

            # Entities section
            f.write(f"## Extracted Entities\n\n")
            f.write(f"**Count:** {len(entities)}\n\n")

            if entities:
                for i, ent in enumerate(entities, 1):
                    f.write(f"### Entity {i}\n\n")
                    f.write(f"- **Text:** {ent['text']}\n")
                    f.write(f"- **Normalized:** {ent['normalized']}\n")
                    f.write(f"- **Type (Full):** {ent['type_full']}\n")
                    f.write(f"  - Primary: {ent['type_primary']}\n")
                    if ent['type_sub1']:
                        f.write(f"  - Sub1: {ent['type_sub1']}\n")
                    if ent['type_sub2']:
                        f.write(f"  - Sub2: {ent['type_sub2']}\n")
                    if ent['type_sub3']:
                        f.write(f"  - Sub3: {ent['type_sub3']}\n")
                    f.write(f"- **Confidence:** {ent['confidence']:.2f}\n")
                    f.write(f"- **Position:** {ent['start']} - {ent['end']}\n")
                    f.write(f"- **Context:** ...{ent['context_before'][-30:]} [{ent['text']}] {ent['context_after'][:30]}...\n")
                    f.write(f"- **Sentence:** {ent['sentence'][:100]}...\n")
                    f.write(f"- **Extraction Method:** {ent['extraction_method']}\n")
                    f.write(f"\n")
            else:
                f.write("No entities extracted.\n\n")

            f.write(f"---\n\n")

            # Relationships section
            f.write(f"## Extracted Relationships\n\n")
            f.write(f"**Count:** {len(relationships)}\n\n")

            if relationships:
                for i, rel in enumerate(relationships, 1):
                    f.write(f"### Relationship {i}\n\n")
                    f.write(f"- **Subject:** {rel['subject_text']} ({rel['subject_type']})\n")
                    f.write(f"- **Predicate:** {rel['predicate']}\n")
                    f.write(f"- **Object:** {rel['object_text']} ({rel['object_type']})\n")
                    f.write(f"- **Confidence:** {rel['confidence']:.2f}\n")
                    f.write(f"- **Context:** {rel['context']}\n")
                    f.write(f"\n")
            else:
                f.write("No relationships extracted.\n\n")

            f.write(f"---\n\n")

            # Analysis section
            f.write(f"## Analysis\n\n")
            f.write(f"### Response Format\n\n")

            # Check for common issues
            if "```json" in response:
                f.write("- Contains markdown code fence (```json)\n")
            if "```" in response:
                f.write("- Contains markdown code fence (```)\n")
            if response.strip().startswith("{"):
                f.write("- Starts with JSON object bracket\n")
            if response.strip().endswith("}"):
                f.write("- Ends with JSON object bracket\n")

            # Check for extra content
            lines = response.strip().split("\n")
            if len(lines) > 50:
                f.write(f"- Response has {len(lines)} lines (potentially verbose)\n")

            if "Summary:" in response or "Explanation:" in response:
                f.write("- WARNING: Response contains explanation text (should be JSON only)\n")

            f.write(f"\n### Extraction Success\n\n")

            # Entity stats
            if entities:
                f.write(f"- Successfully extracted {len(entities)} entities\n")
                avg_conf = sum(e['confidence'] for e in entities) / len(entities)
                f.write(f"- Average entity confidence: {avg_conf:.2f}\n")
                entity_types = {}
                for e in entities:
                    entity_types[e['type_full']] = entity_types.get(e['type_full'], 0) + 1
                f.write(f"- Entity types: {dict(entity_types)}\n")
            else:
                f.write("- No entities extracted (parsing failed or empty response)\n")

            # Relationship stats
            if relationships:
                f.write(f"- Successfully extracted {len(relationships)} relationships\n")
                avg_conf = sum(r['confidence'] for r in relationships) / len(relationships)
                f.write(f"- Average relationship confidence: {avg_conf:.2f}\n")
                predicates = {}
                for r in relationships:
                    predicates[r['predicate']] = predicates.get(r['predicate'], 0) + 1
                f.write(f"- Relationship predicates: {dict(predicates)}\n")
            else:
                f.write("- No relationships extracted (parsing failed or empty response)\n")

            # Comparison with GLiNER approach
            f.write(f"\n### Comparison Notes\n\n")
            f.write(f"- **LLM Approach:** Single prompt extracts both entities and relationships\n")
            f.write(f"- **GLiNER Approach:** Two-step process (GLiNER entities → vLLM relationships)\n")
            f.write(f"- **Advantages:** Unified context, finds conceptual entities, single LLM call\n")
            f.write(f"- **Entities found:** {len(entities)} (compare with GLiNER's entity count)\n")

            f.write(f"\n")

        logger.info(f"Results written to {results_path}")

        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Response length: {len(response)} characters")
        print(f"Entities extracted: {len(entities)}")
        print(f"Relationships extracted: {len(relationships)}")

        if entities:
            print("\nExtracted entities:")
            for i, ent in enumerate(entities[:10], 1):  # Show first 10
                print(f"  {i}. {ent['text']} ({ent['type_full']}) - confidence: {ent['confidence']:.2f}")
            if len(entities) > 10:
                print(f"  ... and {len(entities) - 10} more entities")

        if relationships:
            print("\nExtracted relationships:")
            for i, rel in enumerate(relationships[:10], 1):  # Show first 10
                print(f"  {i}. {rel['subject_text']} --[{rel['predicate']}]--> {rel['object_text']} ({rel['confidence']:.2f})")
            if len(relationships) > 10:
                print(f"  ... and {len(relationships) - 10} more relationships")

        print(f"\nFull results saved to: {results_path}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)

        # Write error to results file
        results_path = Path(__file__).parent / "results.md"
        with open(results_path, "w") as f:
            f.write(f"# KG Extractor Test Results (ERROR)\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Error:** {str(e)}\n\n")
            f.write(f"```\n{e}\n```\n")


if __name__ == "__main__":
    asyncio.run(test_kg_extraction())
