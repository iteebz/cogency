"""Knowledge context namespace - automatic retrieval.

Provides automatic knowledge retrieval for complex queries.
This is ONE OF TWO knowledge retrieval patterns in Cogency:

## DUAL KNOWLEDGE RETRIEVAL ARCHITECTURE

### 1. Automatic Semantic Search (This Module)
- **Purpose**: Background context enrichment
- **Trigger**: Every query automatically  
- **Threshold**: 0.75 (high precision for context)
- **Results**: 2 items max, 200 chars truncated
- **Format**: Context injection as "RELEVANT KNOWLEDGE:" section
- **Location**: cogency.context.knowledge.KnowledgeContext

### 2. Intentional Retrieval (Recall Tool) 
- **Purpose**: Explicit knowledge exploration
- **Trigger**: Agent explicitly calls recall() tool
- **Threshold**: 0.7 (broader results)
- **Results**: 5 items, full content with previews
- **Format**: Formatted tool response with topics/similarities
- **Location**: cogency.memory.recall.Recall

## CURRENT STATUS
- **Database**: .cogency/store.db exists with schema
- **Knowledge vectors**: 0 entries (empty - populated post-conversation)
- **Population**: Automatic via cogency.knowledge.extract after conversations

## TODO: Future Architecture Considerations
- Evaluate threshold differences (0.75 vs 0.7)
- Consider result count optimization (2 vs 5)  
- Review automatic vs intentional retrieval boundaries
- Assess context injection vs tool response formatting efficiency
"""

from typing import Optional


class KnowledgeContext:
    """Knowledge domain context - automatic retrieval."""
    
    def __init__(self, query: str, user_id: str):
        """Initialize knowledge context.
        
        Args:
            query: User query for knowledge retrieval
            user_id: User identifier for scoped knowledge
        """
        self.query = query
        self.user_id = user_id
    
    async def build(self) -> Optional[str]:
        """Build knowledge context with automatic retrieval.
        
        Preserves _get_relevant_knowledge functionality from agents/reason.py.
        
        Returns:
            Knowledge context string or None
        """
        knowledge_content = await self._get_relevant_knowledge()
        
        if knowledge_content:
            return f"RELEVANT KNOWLEDGE:\n{knowledge_content}"
            
        return None
    
    async def _get_relevant_knowledge(self) -> str:
        """Automatically retrieve relevant knowledge for query context.
        
        Let semantic search handle relevance - no brittle heuristics.
        """
        from cogency.events import emit

        try:
            import aiosqlite

            from cogency.providers import detect_embed
            from cogency.semantic import semantic_search
            from cogency.storage import SQLite

            embedder = detect_embed()
            store = SQLite()
            await store._ensure_schema()

            async with aiosqlite.connect(store.db_path) as db:
                search_result = await semantic_search(
                    embedder=embedder,
                    query=self.query,
                    db_connection=db,
                    user_id=self.user_id,
                    top_k=3,  # Limit to most relevant
                    threshold=0.75,  # Higher threshold for automatic retrieval
                )

            if search_result.failure or not search_result.unwrap():
                return ""

            # Format knowledge for context injection
            knowledge_items = []
            for result in search_result.unwrap()[:2]:  # Top 2 results only
                topic = result["metadata"].get("topic", "Knowledge")
                content = result["content"][:200]  # Truncate for context efficiency
                knowledge_items.append(f"- {topic}: {content}...")

            emit("memory", operation="auto_retrieval", results=len(knowledge_items), query=self.query)
            return "\n".join(knowledge_items)

        except Exception as e:
            emit("memory", operation="auto_retrieval", status="error", error=str(e))
            return ""
    
# Removed _is_simple_query() - brittle heuristics deleted
# Semantic search with threshold=0.75 handles relevance filtering