"""LLM-driven user understanding synthesis."""

from datetime import datetime
from typing import Any, Dict, Optional

from cogency.state import Profile


class ImpressionSynthesizer:
    """LLM-driven user understanding synthesis with archival memory integration."""

    def __init__(self, provider, store=None, archival=None):
        self.provider = provider
        self.store = store
        self.archival = archival  # ArchivalMemory instance for topic storage
        self.synthesis_threshold = 3  # Synthesize every N interactions
        self.current_user_id = "default"  # Track current user for load/remember

    async def update_impression(self, user_id: str, interaction_data: Dict[str, Any]) -> Profile:
        """Update user impression from interaction with archival memory integration."""

        # Load existing profile
        profile = await self._load_profile(user_id)

        # Update interaction count only - insights extracted async post-response
        profile.interaction_count += 1
        profile.last_updated = datetime.now()

        # NEW: Process archival memory if enabled
        if self.archival and self._should_archive(interaction_data):
            await self._process_archival_memory(user_id, interaction_data)

        # Save updated profile
        if self.store:
            await self._save_profile(profile)

        return profile

    async def _load_profile(self, user_id: str) -> Profile:
        """Load or create user profile using canonical StateStore methods."""
        if self.store:
            state_key = f"{user_id}:default"
            profile = await self.store.load_user_profile(state_key)
            if profile:
                return profile

        return Profile(user_id=user_id)

    async def _save_profile(self, profile: Profile) -> None:
        """Save profile to storage using canonical StateStore methods."""
        if not self.store:
            return

        state_key = f"{profile.user_id}:default"
        await self.store.save_user_profile(state_key, profile)

    async def load(self, user_id: str = None) -> None:
        """Load memory state for the current user."""
        from cogency.events import emit

        if user_id:
            self.current_user_id = user_id

        emit("memory", operation="load", user_id=self.current_user_id, status="start")

        try:
            # Load profile to validate memory system
            profile = await self._load_profile(self.current_user_id)
            emit(
                "memory",
                operation="load",
                user_id=self.current_user_id,
                status="complete",
                interactions=profile.interaction_count,
            )
        except Exception as e:
            emit(
                "memory",
                operation="load",
                user_id=self.current_user_id,
                status="error",
                error=str(e),
            )
            raise

    async def remember(self, content: str, human: bool = True) -> None:
        """Store interaction for future processing - no LLM calls."""
        from cogency.events import emit

        emit(
            "memory",
            operation="remember",
            user_id=self.current_user_id,
            human=human,
            content_length=len(content),
            status="start",
        )

        try:
            interaction_data = {
                "query" if human else "response": content,
                "success": True,
                "human": human,
            }
            # Pure data storage - no LLM processing
            profile = await self.update_impression(self.current_user_id, interaction_data)

            emit(
                "memory",
                operation="remember",
                user_id=self.current_user_id,
                status="complete",
                total_interactions=profile.interaction_count,
            )
        except Exception as e:
            emit(
                "memory",
                operation="remember",
                user_id=self.current_user_id,
                status="error",
                error=str(e),
            )
            raise
    # Archival Memory Integration Methods

    def _should_archive(self, interaction_data: Dict[str, Any]) -> bool:
        """Determine if interaction should be archived to topic memory."""
        # Archive if it's a user query with substantial content
        query = interaction_data.get("query", "")
        if not query or len(query.strip()) < 20:
            return False
        
        # Skip simple greetings and commands
        query_lower = query.lower().strip()
        skip_patterns = [
            "hello", "hi", "thanks", "thank you", "bye", "goodbye",
            "help", "what can you do", "clear", "reset"
        ]
        
        if any(pattern in query_lower for pattern in skip_patterns):
            return False
        
        return True

    async def _process_archival_memory(self, user_id: str, interaction_data: Dict[str, Any]) -> None:
        """Process interaction for archival memory storage."""
        from cogency.events import emit
        
        try:
            query = interaction_data.get("query", "")
            response = interaction_data.get("response", "")
            
            # Extract topic and create insight content
            topic = await self._extract_topic(query)
            if not topic:
                return
            
            # Create insight content from interaction
            insight_content = await self._create_insight(query, response)
            if not insight_content:
                return
            
            # Store in archival memory
            result = await self.archival.store_insight(
                user_id=user_id,
                topic=topic, 
                content=insight_content,
                conversation_id=interaction_data.get("conversation_id")
            )
            
            emit("memory", operation="archival_update", user_id=user_id, 
                 topic=topic, status="complete")
             
        except Exception as e:
            emit("memory", operation="archival_update", user_id=user_id, 
                 status="error", error=str(e))
            # Non-critical error - don't interrupt main flow

    async def _extract_topic(self, query: str) -> Optional[str]:
        """Extract topic from query using simple heuristics."""
        # Simple keyword-based topic extraction for v1
        # TODO: Could be enhanced with LLM-based extraction later
        
        query_lower = query.lower()
        
        # Programming languages
        if any(lang in query_lower for lang in ["python", "javascript", "react", "typescript", "node"]):
            if "python" in query_lower:
                return "Python"
            elif any(js in query_lower for js in ["javascript", "react", "typescript", "node"]):
                return "JavaScript"
        
        # General topics
        if any(word in query_lower for word in ["database", "sql", "mongodb"]):
            return "Database"
        elif any(word in query_lower for word in ["api", "rest", "graphql", "endpoint"]):
            return "API Development"
        elif any(word in query_lower for word in ["docker", "kubernetes", "deploy", "cloud"]):
            return "DevOps"
        elif any(word in query_lower for word in ["algorithm", "data structure", "optimization"]):
            return "Algorithms"
        elif any(word in query_lower for word in ["ai", "machine learning", "llm", "gpt"]):
            return "AI & ML"
        elif any(word in query_lower for word in ["architecture", "design pattern", "system"]):
            return "Architecture"
        
        # Default fallback - extract first meaningful noun phrase
        # Simple extraction: look for capitalized words or technical terms
        words = query.split()
        for i, word in enumerate(words):
            if len(word) > 3 and (word[0].isupper() or word in ["web", "app", "code", "data"]):
                # Use this word plus next word if available
                if i + 1 < len(words):
                    return f"{word} {words[i+1]}".title()
                return word.title()
        
        # Final fallback
        return "General Knowledge"

    async def _create_insight(self, query: str, response: str = "") -> Optional[str]:
        """Create insight content from query/response pair."""
        if not query:
            return None
        
        # For v1, use the query as the insight
        # Later versions could use LLM to extract key insights from the full exchange
        insight = query.strip()
        
        # Add response context if available and meaningful
        if response and len(response) > 50:
            # Extract key points from response (simple version)
            insight += f"\n\nKey points: {response[:200]}{'...' if len(response) > 200 else ''}"
        
        return insight

    async def load_archival(self, user_id: str = None) -> None:
        """Load archival memory for the current user."""
        if not self.archival:
            return
            
        target_user = user_id or self.current_user_id
        await self.archival.initialize(target_user)