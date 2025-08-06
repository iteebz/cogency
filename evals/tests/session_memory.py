"""Cross-session memory persistence evaluation."""

import tempfile
from pathlib import Path
from typing import Dict

from cogency.config import MemoryConfig, PersistConfig
from cogency.persist.store.filesystem import Filesystem

from ..eval import Eval


class SessionMemory(Eval):
    """Test memory persistence across agent sessions."""

    name = "session_memory"
    description = "Test long-term memory persistence across agent restarts"

    async def run(self) -> Dict:
        # Use temporary directory for isolated testing
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "agent_memory"

            # Create shared store for all sessions
            store = Filesystem(base_dir=str(memory_path))
            memory_config = MemoryConfig(store=store)
            persist_config = PersistConfig(store=store)

            # Session 1: Agent learns something and stores it
            agent_session_1 = self.agent(
                "memory_test_agent", memory=memory_config, persist=persist_config, max_iterations=8
            )

            learning_query = """Remember these three important facts about me:
            1. My favorite programming language is Rust
            2. I work at a company called TechCorp 
            3. My project codename is 'Phoenix'
            
            Confirm you've stored this information."""

            session_1_result = await agent_session_1.run_async(learning_query, user_id="test_user")

            # Verify agent claims to have stored the information
            stored_info = any(
                word in session_1_result.lower()
                for word in ["stored", "remember", "noted", "saved"]
            )

            # Session 2: New agent instance should recall the information
            agent_session_2 = self.agent(
                "memory_test_agent", memory=memory_config, persist=persist_config, max_iterations=8
            )

            recall_queries = [
                "What's my favorite programming language?",
                "Where do I work?",
                "What's my project codename?",
                "Tell me the three facts you know about me.",
            ]

            recall_results = []
            correct_recalls = 0

            for query in recall_queries:
                result = await agent_session_2.run_async(query, user_id="test_user")
                recall_results.append((query, result))

                # Check if response contains the stored information
                result_lower = result.lower()
                contains_rust = "rust" in result_lower
                contains_techcorp = "techcorp" in result_lower
                contains_phoenix = "phoenix" in result_lower

                # Score based on query type
                if "programming language" in query.lower():
                    if contains_rust:
                        correct_recalls += 1
                elif "work" in query.lower():
                    if contains_techcorp:
                        correct_recalls += 1
                elif "codename" in query.lower():
                    if contains_phoenix:
                        correct_recalls += 1
                elif (
                    "three facts" in query.lower()
                    and contains_rust
                    and contains_techcorp
                    and contains_phoenix
                ):
                    correct_recalls += 1

            # Session 3: Test memory persistence with new information
            agent_session_3 = self.agent(
                "memory_test_agent", memory=memory_config, persist=persist_config, max_iterations=8
            )

            update_query = "I just got promoted to Senior Engineer. Update my information."
            session_3_result = await agent_session_3.run_async(update_query, user_id="test_user")

            # Session 4: Verify updated information persists
            agent_session_4 = self.agent(
                "memory_test_agent", memory=memory_config, persist=persist_config, max_iterations=8
            )

            verification_query = "What's my current job title?"
            session_4_result = await agent_session_4.run_async(
                verification_query, user_id="test_user"
            )

            updated_info_persisted = "senior engineer" in session_4_result.lower()

            # Calculate overall performance
            recall_accuracy = correct_recalls / len(recall_queries)
            memory_persistence_works = stored_info and recall_accuracy >= 0.75
            memory_updates_work = updated_info_persisted

            overall_score = (recall_accuracy + (1.0 if memory_updates_work else 0.0)) / 2.0
            passed = memory_persistence_works and memory_updates_work

            all_traces = [
                {
                    "session_1_query": learning_query,
                    "session_1_result": session_1_result[:200] + "..."
                    if len(session_1_result) > 200
                    else session_1_result,
                    "stored_info": stored_info,
                },
                *[
                    {
                        "recall_query": query,
                        "recall_result": result[:200] + "..." if len(result) > 200 else result,
                    }
                    for query, result in recall_results
                ],
                {
                    "update_query": update_query,
                    "update_result": session_3_result[:200] + "..."
                    if len(session_3_result) > 200
                    else session_3_result,
                },
                {
                    "verification_query": verification_query,
                    "verification_result": session_4_result[:200] + "..."
                    if len(session_4_result) > 200
                    else session_4_result,
                    "updated_info_persisted": updated_info_persisted,
                },
            ]

            return {
                "name": self.name,
                "passed": passed,
                "score": overall_score,
                "duration": 0.0,
                "traces": all_traces,
                "metadata": {
                    "recall_accuracy": recall_accuracy,
                    "correct_recalls": correct_recalls,
                    "total_recall_queries": len(recall_queries),
                    "memory_persistence_works": memory_persistence_works,
                    "memory_updates_work": memory_updates_work,
                    "stored_info": stored_info,
                },
            }
