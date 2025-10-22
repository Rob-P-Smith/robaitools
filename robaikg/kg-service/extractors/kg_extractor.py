"""
Knowledge Graph Extractor using vLLM for unified entity and relationship extraction

This module uses an LLM to extract both entities and relationships in a single pass,
providing an alternative to the GLiNER + relationship_extractor pipeline.

Features:
- Simultaneous entity and relationship extraction
- Automatic entity type inference
- JSON response parsing and healing
- GLiNER-compatible entity format output
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import json
import re
import asyncio
from datetime import datetime

from clients.vllm_client import get_vllm_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KGExtractor:
    """Extract entities and relationships using LLM in a single pass with concurrency control"""

    # Class-level semaphore for concurrency control
    _extraction_semaphore: Optional[asyncio.Semaphore] = None
    _semaphore_lock = asyncio.Lock()

    # Tracking metrics
    _active_extractions: int = 0
    _total_queued: int = 0
    _total_completed: int = 0
    _total_failed: int = 0
    _metrics_lock = asyncio.Lock()

    # Relationship types organized by category (same as relation_extractor)
    RELATIONSHIP_TYPES = {
        "technical": [
            "uses", "implements", "extends", "depends_on", "requires",
            "provides", "supports", "integrates_with", "based_on",
            "built_with", "powered_by", "runs_on", "compatible_with"
        ],
        "comparison": [
            "similar_to", "alternative_to", "competes_with", "differs_from",
            "replaces", "supersedes", "evolved_from"
        ],
        "hierarchical": [
            "part_of", "contains", "includes", "composed_of",
            "category_of", "type_of", "instance_of", "subclass_of"
        ],
        "functional": [
            "processes", "generates", "transforms", "analyzes",
            "validates", "handles", "manages", "controls"
        ],
        "development": [
            "developed_by", "maintained_by", "created_by", "designed_by",
            "contributed_to", "sponsored_by"
        ],
        "documentation": [
            "documented_in", "described_in", "defined_in",
            "referenced_in", "mentioned_in"
        ],
        "configuration": [
            "configured_with", "settings_for", "parameter_of",
            "option_for", "enabled_by"
        ],
        "performance": [
            "optimizes", "improves", "accelerates", "scales_with",
            "benchmarked_against"
        ]
    }

    # Common entity type categories for guidance
    ENTITY_TYPE_EXAMPLES = [
        "Framework", "Library", "Language", "Technology", "Platform",
        "Concept", "Algorithm", "Pattern", "Tool", "Service",
        "Database", "Protocol", "Format", "Standard", "API",
        "Person", "Organization", "Product", "Version", "Date"
    ]

    def __init__(self):
        """Initialize KG extractor"""
        self.vllm_client = None  # Will be initialized in async methods
        self.min_confidence = settings.RELATION_MIN_CONFIDENCE
        logger.info(f"KG Extractor initialized (LLM-based, max concurrent extractions: {settings.MAX_CONCURRENT_EXTRACTIONS})")

    @classmethod
    async def _get_semaphore(cls) -> asyncio.Semaphore:
        """Get or create the class-level semaphore (thread-safe)"""
        if cls._extraction_semaphore is None:
            async with cls._semaphore_lock:
                if cls._extraction_semaphore is None:
                    cls._extraction_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_EXTRACTIONS)
                    logger.info(f"🔒 Extraction semaphore initialized: {settings.MAX_CONCURRENT_EXTRACTIONS} slots")
        return cls._extraction_semaphore

    @classmethod
    async def _update_metrics(cls, action: str):
        """Update extraction metrics thread-safely"""
        async with cls._metrics_lock:
            if action == "queue":
                cls._total_queued += 1
            elif action == "start":
                cls._active_extractions += 1
            elif action == "complete":
                cls._active_extractions -= 1
                cls._total_completed += 1
            elif action == "fail":
                cls._active_extractions -= 1
                cls._total_failed += 1

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Get current extraction metrics (synchronous snapshot)"""
        return {
            "active_extractions": cls._active_extractions,
            "total_queued": cls._total_queued,
            "total_completed": cls._total_completed,
            "total_failed": cls._total_failed,
            "max_concurrent": settings.MAX_CONCURRENT_EXTRACTIONS,
            "slots_available": settings.MAX_CONCURRENT_EXTRACTIONS - cls._active_extractions
        }

    async def _ensure_vllm_client(self):
        """Ensure vLLM client is initialized (lazy async initialization)"""
        if self.vllm_client is None:
            self.vllm_client = await get_vllm_client()
            await self.vllm_client.ensure_model()
            logger.info(f"vLLM client ready with model: {self.vllm_client.model_name}")
        return self.vllm_client

    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for LLM to extract both entities and relationships"""

        # Format relationship types by category
        rel_types_formatted = []
        for category, types in self.RELATIONSHIP_TYPES.items():
            rel_types_formatted.append(f"- **{category.title()}**: {', '.join(types)}")
        rel_types_formatted = "\n".join(rel_types_formatted)

        # Format entity type examples
        entity_types_formatted = ", ".join(self.ENTITY_TYPE_EXAMPLES)

        prompt = f"""You are an expert at extracting knowledge graphs from technical documentation.

Your task is to extract BOTH entities and relationships from the text below.

[[[
**Text:**
{text}
]]]

**Task 1: Extract Entities**
Identify all significant entities in the text. For each entity:
- Determine its type from categories like: {entity_types_formatted}
- Assign a confidence score (0.0 to 1.0)
- Find its exact position in the text

Focus on:
- Technologies (frameworks, libraries, languages, tools)
- Concepts (patterns, algorithms, methodologies)
- Products and services
- Organizations and people
- Processes and operations (e.g., "text_normalization", "removing_stopwords")

**Task 2: Extract Relationships**
Identify meaningful relationships between the entities you found.

(((
**Relationship Types (organized by category):**
{rel_types_formatted}
)))

Use the most appropriate relationship type from above, or create similar snake_case predicates if needed.

**Output Format:**
Return a JSON object with two arrays:

{{
  "entities": [
    {{
      "text": "FastAPI",
      "type": "Framework::Backend::Python",
      "confidence": 0.95,
      "start": 0,
      "end": 7
    }},
    {{
      "text": "Perplexity",
      "type": "Concept::Metric::Statistical",
      "confidence": 0.95,
      "start": 100,
      "end": 110
    }},
    ...
  ],
  "relationships": [
    {{
      "subject": "FastAPI",
      "predicate": "uses",
      "object": "Pydantic",
      "confidence": 0.88,
      "context": "FastAPI uses Pydantic for data validation and serialization"
    }},
    ...
  ]
}}

**Important Rules:**

***ENTITY EXTRACTION:***
1. Extract ALL significant entities from the text, including:
   - Technologies (frameworks, libraries, languages, tools)
   - Concepts (patterns, algorithms, methodologies, abstract ideas)
   - Processes (normalization, tokenization, cleaning, removing)
   - Data types (numbers, punctuation, whitespace, strings)
   - Products, organizations, people
2. Entity "text" must be the exact text from the document
3. Entity "type" should be HIERARCHICAL using :: separator (e.g., "Framework::Backend::Python", "Concept::DataType")
   - First level: Primary category (Framework, Library, Language, Concept, Process, DataType, etc.)
   - Second level: Subcategory (Backend, Frontend, Metric, Algorithm, TextProcessing, etc.)
   - Third level: Specific detail (Python, JavaScript, Statistical, etc.)
   - Use 1-3 levels as appropriate (flat "Concept" is ok if no subcategories apply)
4. Entity "start" and "end" are character positions in the text
5. Be LIBERAL with entity extraction - if you might reference it in a relationship, extract it as an entity!
6. Deduplicate entities (same entity mentioned multiple times = one entry with first position)

***RELATIONSHIP EXTRACTION:***
7. **CRITICAL:** Relationship "subject" and "object" must EXACTLY match an entity "text" from your entities array
8. **VERIFY BEFORE CREATING:** Before adding a relationship, check that BOTH the subject AND object exist in your entities list
9. **DO NOT** reference entities that you didn't extract in step 1
10. **DO NOT** invent new entity names in relationships - use EXACT text from entities array
11. Use lowercase snake_case for predicates (e.g., "uses", "implements", "part_of", "removes", "processes")
12. Confidence should reflect clarity (0.5-0.7 = uncertain, 0.7-0.9 = clear, 0.9-1.0 = explicit)
13. Context should be a relevant quote from the text (50-100 words)

***CONSISTENCY CHECK:***
14. After generating all relationships, verify EACH ONE:
    - Does the subject text EXACTLY match an entity in your entities array?
    - Does the object text EXACTLY match an entity in your entities array?
    - If NO to either question, REMOVE that relationship!

Return ONLY the JSON object, no additional text.
DO NOT ADD EXPLANATIONS OR SUMMARIES.
DO NOT ADD MARKDOWN CODE FENCES.

When you have finished generating the complete JSON object, stop immediately with your normal end-of-generation token."""

        return prompt

    def _heal_truncated_json(self, response: str) -> str:
        """
        Heal incomplete JSON object from truncated LLM response.

        Our expected structure:
        {
          "entities": [...],
          "relationships": [...]
        }

        Strategy:
        1. Find last complete entity/relationship object
        2. Close incomplete arrays properly
        3. Close main object
        """
        # Find object start
        start_idx = response.find('{')
        if start_idx == -1:
            logger.warning("No JSON object found in response")
            return '{"entities": [], "relationships": []}'

        # Check if already properly closed
        stripped = response.rstrip()
        if stripped.endswith('}'):
            # Quick validation - count braces and brackets
            open_braces = stripped.count('{')
            close_braces = stripped.count('}')
            open_brackets = stripped.count('[')
            close_brackets = stripped.count(']')

            if open_braces == close_braces and open_brackets == close_brackets:
                return response  # Already valid

        logger.warning("Detected incomplete JSON, attempting to heal...")

        # Find the last complete object or array element
        # Look for patterns like: }, or }] or }
        last_complete_idx = -1

        # Search backwards for last complete structure
        for i in range(len(response) - 1, start_idx, -1):
            char = response[i]

            # Found closing brace/bracket - this might be a complete structure
            if char in ['}', ']']:
                last_complete_idx = i
                break

        if last_complete_idx == -1:
            logger.error("No complete structures found, returning empty arrays")
            return '{"entities": [], "relationships": []}'

        # Truncate to last complete structure
        healed = response[:last_complete_idx + 1]

        # Now intelligently close based on what's open
        # Count nested structures
        open_braces = healed.count('{')
        close_braces = healed.count('}')
        open_brackets = healed.count('[')
        close_brackets = healed.count(']')

        logger.debug(f"Healing stats - Braces: {open_braces} open, {close_braces} closed | Brackets: {open_brackets} open, {close_brackets} closed")

        # Check if we're inside an array by looking at the structure
        # If we have "entities": [ or "relationships": [, we need to close them
        in_entities_array = '"entities"' in healed and healed.count('"entities"') > healed.count('"entities": []')
        in_relationships_array = '"relationships"' in healed and healed.count('"relationships"') > healed.count('"relationships": []')

        # Close arrays first (inner structures)
        if open_brackets > close_brackets:
            missing_brackets = open_brackets - close_brackets
            logger.debug(f"Adding {missing_brackets} closing brackets for arrays")
            for _ in range(missing_brackets):
                # Check if we need a newline and indentation
                if healed.rstrip().endswith(',') or healed.rstrip().endswith('{') or healed.rstrip().endswith('['):
                    healed += '\n  ]'
                else:
                    healed += '\n  ]'

        # Close objects (outer structures)
        if open_braces > close_braces:
            missing_braces = open_braces - close_braces
            logger.debug(f"Adding {missing_braces} closing braces for objects")
            for _ in range(missing_braces):
                healed += '\n}'

        # Final validation
        final_open_braces = healed.count('{')
        final_close_braces = healed.count('}')
        final_open_brackets = healed.count('[')
        final_close_brackets = healed.count(']')

        if final_open_braces != final_close_braces or final_open_brackets != final_close_brackets:
            logger.error(f"Healing failed - Braces: {final_open_braces}/{final_close_braces}, Brackets: {final_open_brackets}/{final_close_brackets}")
            logger.error(f"Returning fallback empty structure")
            return '{"entities": [], "relationships": []}'

        truncated_chars = len(response) - len(healed)
        logger.warning(f"Successfully healed truncated JSON - removed {truncated_chars} incomplete characters")

        return healed

    def _sanitize_escape_sequences(self, text: str) -> str:
        r"""
        Fix invalid escape sequences in LLM-generated JSON using multi-pass approach.

        Common issues:
        - Backslash followed by invalid escape character (like \d in regex)
        - Already escaped sequences like \\\\ that need normalization
        - Single backslash at end of string
        - Invalid unicode escapes

        Valid JSON escape sequences: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX

        Args:
            text: JSON string with potentially invalid escapes

        Returns:
            Sanitized JSON string
        """
        import re

        max_passes = 3
        for pass_num in range(max_passes):
            logger.debug(f"Sanitization pass {pass_num + 1}/{max_passes}")

            original_text = text

            # Pass 1: Fix invalid unicode escapes (truncated \uXXXX)
            # Pattern: \u followed by less than 4 hex digits before a non-hex char
            text = re.sub(r'\\u([0-9a-fA-F]{0,3})(?![0-9a-fA-F])', r'\\\\u\1', text)

            # Pass 2: Fix backslashes followed by invalid escape characters
            # Valid JSON escapes are: " \ / b f n r t u
            # This finds: \ followed by anything that's NOT a valid escape char
            # We need to be careful about already-escaped backslashes (\\)

            # First, temporarily protect valid escape sequences by marking them
            # Use unique markers that won't conflict with JSON content
            protected = text
            protected = protected.replace('\\"', '___QUOTE___')
            protected = protected.replace('\\\\', '___BACKSLASH___')
            protected = protected.replace('\\/', '___SLASH___')
            protected = protected.replace('\\b', '___BACKSPACE___')
            protected = protected.replace('\\f', '___FORMFEED___')
            protected = protected.replace('\\n', '___NEWLINE___')
            protected = protected.replace('\\r', '___RETURN___')
            protected = protected.replace('\\t', '___TAB___')
            # Unicode escapes: \uXXXX (4 hex digits)
            protected = re.sub(r'\\u([0-9a-fA-F]{4})', r'___UNICODE\1___', protected)

            # Now any remaining backslashes are invalid - escape them
            protected = protected.replace('\\', '\\\\')

            # Restore the protected sequences
            protected = protected.replace('___QUOTE___', '\\"')
            protected = protected.replace('___BACKSLASH___', '\\\\')
            protected = protected.replace('___SLASH___', '\\/')
            protected = protected.replace('___BACKSPACE___', '\\b')
            protected = protected.replace('___FORMFEED___', '\\f')
            protected = protected.replace('___NEWLINE___', '\\n')
            protected = protected.replace('___RETURN___', '\\r')
            protected = protected.replace('___TAB___', '\\t')
            protected = re.sub(r'___UNICODE([0-9a-fA-F]{4})___', r'\\u\1', protected)

            text = protected

            # Check if we made any changes
            if text == original_text:
                logger.debug(f"No changes in pass {pass_num + 1}, sanitization complete")
                break

        logger.debug(f"Escape sequence sanitization complete after {pass_num + 1} passes")

        return text

    def _parse_llm_response(
        self,
        response: str,
        text: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parse LLM response and extract entities and relationships

        Args:
            response: Raw LLM JSON response
            text: Original document text

        Returns:
            Tuple of (entities_list, relationships_lists)
        """
        # Iteratively clean response until we get pure JSON
        # Keep peeling away outer layers (markdown fences, extra text, etc.)
        # until response starts with { and ends with }
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            # Strip whitespace
            response = response.strip()

            # Check if we have clean JSON (starts with { ends with })
            if response.startswith('{') and response.endswith('}'):
                logger.debug(f"Clean JSON found after {iteration} cleaning iterations")
                break

            # Try to extract from markdown code fences
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response, re.DOTALL)
            if json_match:
                logger.debug(f"Iteration {iteration}: Extracting from markdown fences")
                response = json_match.group(1)
                iteration += 1
                continue

            # Try to find JSON object boundaries
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                logger.debug(f"Iteration {iteration}: Extracting by object boundaries")
                response = response[start_idx:end_idx + 1]
                iteration += 1
                continue

            # No more cleaning possible
            logger.warning(f"Could not extract clean JSON after {iteration} iterations")
            break

        # Heal any truncated JSON
        response = self._heal_truncated_json(response)

        # Sanitize escape sequences before parsing
        response = self._sanitize_escape_sequences(response)

        try:
            # DEBUG: Dump exact response for troubleshooting (only in debug mode)
            if settings.DEBUG:
                logger.info("=" * 80)
                logger.info("RAW RESPONSE AFTER CLEANING (character-by-character):")
                logger.info("=" * 80)
                for i, line in enumerate(response.split('\n'), 1):
                    logger.info(f"Line {i:4d}: {repr(line)}")
                logger.info("=" * 80)
                logger.info(f"Total length: {len(response)} characters")
                logger.info("=" * 80)

            # Parse JSON
            data = json.loads(response)

            if not isinstance(data, dict):
                logger.warning("LLM response is not a JSON object")
                return [], []

            entities_raw = data.get("entities", [])
            relationships_raw = data.get("relationships", [])

            if not isinstance(entities_raw, list):
                logger.warning("'entities' field is not a list")
                entities_raw = []

            if not isinstance(relationships_raw, list):
                logger.warning("'relationships' field is not a list")
                relationships_raw = []

            logger.info(f"Parsed LLM response: {len(entities_raw)} entities, {len(relationships_raw)} relationships")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response preview: {response[:500]}")
            return [], []

        # Process entities into GLiNER-compatible format
        entities = self._process_entities(entities_raw, text)

        # Process relationships
        relationships = self._process_relationships(relationships_raw, entities)

        return entities, relationships

    def _process_entities(
        self,
        entities_raw: List[Dict[str, Any]],
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Convert LLM entities to GLiNER-compatible format

        Args:
            entities_raw: Raw entity dicts from LLM
            text: Original document text

        Returns:
            List of GLiNER-compatible entity dicts
        """
        entities = []
        seen_normalized = set()

        for ent_raw in entities_raw:
            try:
                # Required fields
                if not all(k in ent_raw for k in ["text", "type", "confidence"]):
                    logger.debug(f"Skipping entity missing required fields: {ent_raw}")
                    continue

                entity_text = ent_raw["text"].strip()
                entity_type = ent_raw["type"].strip()
                confidence = float(ent_raw["confidence"])

                # Validate confidence
                if confidence < self.min_confidence:
                    continue

                # Normalize entity name
                normalized = entity_text.lower().strip()

                # Deduplicate (keep first occurrence)
                if normalized in seen_normalized:
                    continue
                seen_normalized.add(normalized)

                # Get position (use LLM-provided if available, otherwise search)
                start_pos = ent_raw.get("start", text.find(entity_text))
                end_pos = ent_raw.get("end", start_pos + len(entity_text))

                # Validate position
                if start_pos < 0 or end_pos < 0 or start_pos >= end_pos:
                    # Fallback: search for entity in text
                    start_pos = text.lower().find(normalized)
                    if start_pos >= 0:
                        end_pos = start_pos + len(entity_text)
                    else:
                        # Can't find entity in text, skip it
                        logger.debug(f"Cannot find entity '{entity_text}' in text")
                        continue

                # Extract context
                context = self._get_context(text, start_pos, end_pos)

                # Parse hierarchical type (supports Type::Subtype::Detail format)
                if "::" in entity_type:
                    type_parts = entity_type.split("::")
                    type_primary = type_parts[0] if len(type_parts) > 0 else entity_type
                    type_sub1 = type_parts[1] if len(type_parts) > 1 else None
                    type_sub2 = type_parts[2] if len(type_parts) > 2 else None
                    type_sub3 = type_parts[3] if len(type_parts) > 3 else None
                    type_full = entity_type
                else:
                    # Flat type - use as primary only
                    type_primary = entity_type
                    type_sub1 = None
                    type_sub2 = None
                    type_sub3 = None
                    type_full = entity_type

                # Build GLiNER-compatible entity dict
                entity = {
                    # Identity
                    "text": entity_text,
                    "normalized": normalized,
                    "start": start_pos,
                    "end": end_pos,

                    # Type (hierarchical or flat)
                    "type_full": type_full,
                    "type_primary": type_primary,
                    "type_sub1": type_sub1,
                    "type_sub2": type_sub2,
                    "type_sub3": type_sub3,

                    # Confidence
                    "confidence": confidence,

                    # Context
                    "context_before": context["context_before"],
                    "context_after": context["context_after"],
                    "sentence": context["sentence"],

                    # Metadata
                    "extraction_method": "llm"
                }

                entities.append(entity)

            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Invalid entity format: {e} - {ent_raw}")
                continue

        logger.info(f"Processed {len(entities)} valid entities from LLM response")
        return entities

    def _process_relationships(
        self,
        relationships_raw: List[Dict[str, Any]],
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process and validate relationships against extracted entities

        Args:
            relationships_raw: Raw relationship dicts from LLM
            entities: Processed entity list

        Returns:
            List of validated relationship dicts
        """
        # Build entity lookup
        entity_lookup = {}
        for ent in entities:
            entity_lookup[ent["text"].lower()] = ent
            entity_lookup[ent["normalized"]] = ent

        relationships = []
        rejected_count = 0

        for rel_raw in relationships_raw:
            try:
                # Required fields
                if not all(k in rel_raw for k in ["subject", "predicate", "object", "confidence"]):
                    rejected_count += 1
                    logger.warning(f"❌ Relationship missing required fields: {rel_raw}")
                    continue

                subject_text = rel_raw["subject"].strip()
                object_text = rel_raw["object"].strip()
                predicate = rel_raw["predicate"].lower().replace(" ", "_")
                confidence = float(rel_raw["confidence"])
                context = rel_raw.get("context", "")

                # Validate confidence
                if confidence < self.min_confidence:
                    rejected_count += 1
                    logger.warning(f"❌ Relationship rejected (low confidence {confidence}): {subject_text} -> {object_text}")
                    continue

                # Find matching entities
                subject_entity = entity_lookup.get(subject_text.lower())
                object_entity = entity_lookup.get(object_text.lower())

                if not subject_entity:
                    rejected_count += 1
                    logger.warning(f"❌ Relationship rejected (subject not found): '{subject_text}' -> {object_text}")
                    logger.warning(f"   Available entities: {list(entity_lookup.keys())[:10]}")
                    continue

                if not object_entity:
                    rejected_count += 1
                    logger.warning(f"❌ Relationship rejected (object not found): {subject_text} -> '{object_text}'")
                    logger.warning(f"   Available entities: {list(entity_lookup.keys())[:10]}")
                    continue

                # Skip self-relationships
                if subject_entity["normalized"] == object_entity["normalized"]:
                    rejected_count += 1
                    logger.warning(f"❌ Relationship rejected (self-reference): {subject_text} -> {object_text}")
                    continue

                # Build validated relationship
                relationship = {
                    "subject_text": subject_entity["text"],
                    "subject_normalized": subject_entity["normalized"],
                    "subject_type": subject_entity["type_full"],
                    "predicate": predicate,
                    "object_text": object_entity["text"],
                    "object_normalized": object_entity["normalized"],
                    "object_type": object_entity["type_full"],
                    "confidence": confidence,
                    "context": context[:500],
                    "subject_start": subject_entity["start"],
                    "subject_end": subject_entity["end"],
                    "object_start": object_entity["start"],
                    "object_end": object_entity["end"]
                }

                relationships.append(relationship)

            except (KeyError, ValueError, TypeError) as e:
                rejected_count += 1
                logger.warning(f"❌ Relationship rejected (format error): {e} - {rel_raw}")
                continue

        logger.info(f"Processed {len(relationships)} valid relationships from LLM response")
        if rejected_count > 0:
            logger.warning(f"⚠️  Rejected {rejected_count} relationships out of {len(relationships_raw)} total")
            logger.warning(f"⚠️  Acceptance rate: {len(relationships)}/{len(relationships_raw)} ({100*len(relationships)/len(relationships_raw) if relationships_raw else 0:.1f}%)")
        return relationships

    def _get_context(
        self,
        text: str,
        start: int,
        end: int,
        window: int = 50
    ) -> Dict[str, str]:
        """
        Extract context around an entity mention

        Args:
            text: Full text
            start: Entity start position
            end: Entity end position
            window: Characters to include before/after

        Returns:
            dict with context_before, context_after, sentence
        """
        # Get surrounding context
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)

        context_before = text[context_start:start].strip()
        context_after = text[end:context_end].strip()

        # Try to extract full sentence
        sentence_start = text.rfind('.', 0, start) + 1
        sentence_end = text.find('.', end)
        if sentence_end == -1:
            sentence_end = len(text)

        sentence = text[sentence_start:sentence_end].strip()

        return {
            "context_before": context_before,
            "context_after": context_after,
            "sentence": sentence
        }

    async def extract_kg(
        self,
        text: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract knowledge graph (entities and relationships) from text using LLM
        with concurrency control (max 4 concurrent extractions)

        Args:
            text: Full document text

        Returns:
            Tuple of (entities, relationships)
            - entities: List of GLiNER-compatible entity dicts
            - relationships: List of relationship dicts
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for KG extraction")
            return [], []

        # Ensure vLLM client is initialized
        await self._ensure_vllm_client()

        # Build prompt
        prompt = self._build_extraction_prompt(text)
        logger.debug(f"Built KG extraction prompt, length: {len(prompt)}")

        # Get semaphore for concurrency control
        semaphore = await self._get_semaphore()

        # Track queueing
        await self._update_metrics("queue")
        metrics = self.get_metrics()

        # Check if we need to wait
        if metrics["slots_available"] <= 0:
            logger.warning(f"⏳ Waiting for extraction slot... ({metrics['active_extractions']}/{metrics['max_concurrent']} slots in use)")

        # Acquire semaphore (will wait if at capacity)
        async with semaphore:
            # Update metrics - we're now active
            await self._update_metrics("start")
            current_metrics = self.get_metrics()
            logger.info(f"🔓 Starting extraction ({current_metrics['active_extractions']}/{current_metrics['max_concurrent']} slots in use)")

            # Call vLLM for extraction
            try:
                logger.info("Calling vLLM for knowledge graph extraction...")
                response = await self.vllm_client.complete(
                    prompt=prompt,
                    max_tokens=131072,  # Very large for comprehensive extraction from long documents
                    temperature=settings.VLLM_TEMPERATURE,
                    repetition_penalty=1.1
                )
                logger.info(f"vLLM response received, length: {len(response)}")
                logger.debug(f"RAW RESPONSE START >>>>\n{response}\n<<<< RAW RESPONSE END")

                # Parse response
                entities, relationships = self._parse_llm_response(response, text)

                await self._update_metrics("complete")
                logger.info(f"✅ KG extraction complete: {len(entities)} entities, {len(relationships)} relationships")
                return entities, relationships

            except Exception as e:
                await self._update_metrics("fail")
                logger.error(f"KG extraction failed: {e}")
                return [], []


# Global instance
_kg_extractor: Optional[KGExtractor] = None


def get_kg_extractor() -> KGExtractor:
    """Get global KG extractor instance"""
    global _kg_extractor
    if _kg_extractor is None:
        _kg_extractor = KGExtractor()
    return _kg_extractor
