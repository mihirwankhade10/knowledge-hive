"""
KnowledgeHive - LLM Prompt Templates

All prompt templates used by agents. Centralized here for easy tuning.
"""

# =============================================================================
# Entity & Relationship Extraction (Graph Agent)
# =============================================================================

ENTITY_EXTRACTION_PROMPT = """You are an expert knowledge analyst. Extract key entities from the following text.

For each entity, provide:
- name: The entity name
- type: One of [PERSON, ORGANIZATION, TECHNOLOGY, CONCEPT, PROCESS, DOCUMENT, LOCATION, EVENT, PRODUCT]
- description: A brief one-line description

TEXT:
{text}

Respond ONLY with a valid JSON array of objects. Example:
[
  {{"name": "Machine Learning", "type": "CONCEPT", "description": "A subset of AI that learns from data"}},
  {{"name": "Google", "type": "ORGANIZATION", "description": "A technology company"}}
]

If no entities are found, respond with an empty array: []
"""

RELATIONSHIP_EXTRACTION_PROMPT = """You are an expert knowledge analyst. Given these entities and the source text, extract relationships between them.

ENTITIES:
{entities}

TEXT:
{text}

For each relationship, provide:
- source: Source entity name (must match an entity above)
- target: Target entity name (must match an entity above)
- relationship: One of [RELATES_TO, PART_OF, USES, CREATED_BY, DEPENDS_ON, IMPLEMENTS, MANAGES, CONTAINS]
- description: Brief description of the relationship

Respond ONLY with a valid JSON array. Example:
[
  {{"source": "Machine Learning", "target": "AI", "relationship": "PART_OF", "description": "ML is a subset of AI"}}
]

If no relationships are found, respond with an empty array: []
"""

# =============================================================================
# Answer Generation (Response Agent)
# =============================================================================

ANSWER_GENERATION_PROMPT = """You are KnowledgeHive, an enterprise knowledge assistant. Answer the user's question using ONLY the provided context.

RULES:
1. Use ONLY the information from the context below. Do NOT make up information.
2. If the context doesn't contain enough information, say so clearly.
3. Cite your sources using [Source N] notation.
4. Be concise but thorough.
5. Structure your answer with clear formatting.

CONTEXT:
{context}

GRAPH CONTEXT:
{graph_context}

QUESTION: {question}

Provide a well-structured answer with source citations:"""

# =============================================================================
# Validation (Validation Agent)
# =============================================================================

VALIDATION_PROMPT = """You are a fact-checking assistant. Evaluate how well the following retrieved context answers the given question.

QUESTION: {question}

RETRIEVED CONTEXT:
{context}

For each piece of context, evaluate:
1. Relevance (0.0 to 1.0): How relevant is this to the question?
2. Sufficiency: Does the combined context sufficiently answer the question?

Respond with a JSON object:
{{
  "relevance_scores": [0.0 to 1.0 for each context piece],
  "overall_confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of your assessment"
}}
"""
