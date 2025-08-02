⏺ COGENCY v1.0.0 STATE SPECIFICATION - FINAL LOCKED VERSION

  Status: COUNCIL APPROVED - LOCKED FOR v1.0.0Authors: Claude Code, Claude Prime, ChatGPT, Kitsuragi, GeminiDate: 2025-01-02Lock Status: 🔒 NO CHANGES BEYOND v1.0.0

  ---
  🎯 EXECUTIVE SUMMARY

  This specification defines Cogency's state architecture for v1.0.0 and all subsequent versions. No architectural changes will be made beyond this release. The
  design balances breakthrough innovation (situated memory) with implementation simplicity, addressing all council concerns while preserving the core cognitive
  advances.

  ---
  🏗️ CORE ARCHITECTURE - FINAL

  1. Execution State (Simplified Implementation)

  @dataclass
  class ExecutionState:
      """Pure execution tracking - minimal ceremony."""

      # Core Identity
      query: str
      user_id: str = "default"

      # Loop Control
      iteration: int = 0
      max_iterations: int = 10
      mode: str = "adapt"  # "fast" | "deep" | "adapt"
      stop_reason: Optional[str] = None

      # Communication
      messages: List[Dict[str, str]] = field(default_factory=list)
      response: Optional[str] = None

      # Tool Execution (Dictionary-based - Gemini's simplification)
      pending_calls: List[Dict[str, Any]] = field(default_factory=list)
      completed_calls: List[Dict[str, Any]] = field(default_factory=list)

      # System
      debug: bool = False
      notifications: List[Dict[str, Any]] = field(default_factory=list)

      def add_message(self, role: str, content: str) -> None:
          """Add to conversation history."""
          self.messages.append({
              "role": role,
              "content": content,
              "timestamp": datetime.now().isoformat()
          })

      def set_tool_calls(self, calls: List[Dict[str, Any]]) -> None:
          """Set pending tool calls from reasoning."""
          self.pending_calls = calls

      def complete_tool_calls(self, results: List[Dict[str, Any]]) -> None:
          """Process completed tool results."""
          self.completed_calls.extend(results)
          self.pending_calls.clear()

      def should_continue(self) -> bool:
          """Determine if reasoning loop should continue."""
          return (
              self.iteration < self.max_iterations
              and not self.response
              and not self.stop_reason
              and bool(self.pending_calls)
          )

      def advance_iteration(self) -> None:
          """Move to next reasoning iteration."""
          self.iteration += 1

  2. Reasoning Context (Structured Cognition)

  @dataclass
  class ReasoningContext:
      """Structured reasoning memory - no string-based fields."""

      # Core Cognition (Structured Facts - ChatGPT's requirement)
      goal: str = ""
      facts: Dict[str, Any] = field(default_factory=dict)
      strategy: str = ""
      insights: List[str] = field(default_factory=list)

      # Reasoning History (Simplified - Gemini's requirement)
      thoughts: List[Dict[str, Any]] = field(default_factory=list)

      def add_insight(self, insight: str) -> None:
          """Add new insight with bounded growth."""
          if insight and insight.strip() and insight not in self.insights:
              self.insights.append(insight.strip())
              # Prevent unbounded growth - keep last 10
              if len(self.insights) > 10:
                  self.insights = self.insights[-10:]

      def update_facts(self, key: str, value: Any) -> None:
          """Update structured knowledge."""
          if key and key.strip():
              self.facts[key] = value
              # Prevent unbounded growth - keep last 20 facts
              if len(self.facts) > 20:
                  oldest_keys = list(self.facts.keys())[:-20]
                  for old_key in oldest_keys:
                      del self.facts[old_key]

      def record_thinking(self, thinking: str, tool_calls: List[Dict[str, Any]]) -> None:
          """Record reasoning step."""
          thought = {
              "thinking": thinking,
              "tool_calls": tool_calls,
              "timestamp": datetime.now().isoformat()
          }
          self.thoughts.append(thought)
          # Keep last 5 thoughts for context
          if len(self.thoughts) > 5:
              self.thoughts = self.thoughts[-5:]

      def compress_for_context(self, max_tokens: int = 1000) -> str:
          """Intelligent compression for LLM context."""
          sections = []

          if self.goal:
              sections.append(f"GOAL: {self.goal}")

          if self.strategy:
              sections.append(f"STRATEGY: {self.strategy}")

          if self.facts:
              # Show most recent facts
              recent_facts = list(self.facts.items())[-5:]
              facts_str = "; ".join(f"{k}: {v}" for k, v in recent_facts)
              sections.append(f"FACTS: {facts_str}")

          if self.insights:
              # Show most recent insights
              recent_insights = self.insights[-3:]
              insights_str = "; ".join(recent_insights)
              sections.append(f"INSIGHTS: {insights_str}")

          if self.thoughts:
              # Show last thought summary
              last_thought = self.thoughts[-1]
              sections.append(f"LAST THINKING: {last_thought['thinking'][:200]}")

          result = "\n".join(sections)
          return result[:max_tokens] if len(result) > max_tokens else result

  3. Complete Agent State

  class AgentState:
      """Complete agent state - execution + reasoning + situated memory."""

      def __init__(
          self, 
          query: str, 
          user_id: str = "default", 
          user_profile: Optional['UserProfile'] = None
      ):
          self.execution = ExecutionState(query=query, user_id=user_id)
          self.reasoning = ReasoningContext(goal=query)
          self.user_profile = user_profile  # Situated memory

      def get_situated_context(self) -> str:
          """Get user context for prompt injection."""
          if not self.user_profile:
              return ""

          context = self.user_profile.compress_for_injection()
          return f"USER CONTEXT:\n{context}\n\n" if context else ""

      def update_from_reasoning(self, reasoning_data: Dict[str, Any]) -> None:
          """Update state from LLM reasoning response."""
          # Record thinking
          thinking = reasoning_data.get("thinking", "")
          tool_calls = reasoning_data.get("tool_calls", [])

          if thinking:
              self.reasoning.record_thinking(thinking, tool_calls)

          # Set tool calls for execution
          if tool_calls:
              self.execution.set_tool_calls(tool_calls)

          # Update reasoning context
          context_updates = reasoning_data.get("context_updates", {})
          if context_updates:
              if "goal" in context_updates:
                  self.reasoning.goal = context_updates["goal"]
              if "strategy" in context_updates:
                  self.reasoning.strategy = context_updates["strategy"]
              if "insights" in context_updates and isinstance(context_updates["insights"], list):
                  for insight in context_updates["insights"]:
                      self.reasoning.add_insight(insight)

          # Handle direct response
          if "response" in reasoning_data and reasoning_data["response"]:
              self.execution.response = reasoning_data["response"]

          # Handle mode switching
          if "switch_mode" in reasoning_data and reasoning_data["switch_mode"]:
              new_mode = reasoning_data["switch_mode"]
              if new_mode in ["fast", "deep", "adapt"]:
                  self.execution.mode = new_mode

  ---
  🧠 SITUATED MEMORY ARCHITECTURE - BREAKTHROUGH COMPONENT

  1. User Profile (The Innovation)

  @dataclass
  class UserProfile:
      """Persistent user understanding - builds over time."""

      user_id: str

      # Core Understanding
      preferences: Dict[str, Any] = field(default_factory=dict)
      goals: List[str] = field(default_factory=list)
      expertise_areas: List[str] = field(default_factory=list)
      communication_style: str = ""

      # Contextual Knowledge
      projects: Dict[str, str] = field(default_factory=dict)
      interests: List[str] = field(default_factory=list)
      constraints: List[str] = field(default_factory=list)

      # Interaction Patterns
      success_patterns: List[str] = field(default_factory=list)
      failure_patterns: List[str] = field(default_factory=list)

      # Metadata
      created_at: datetime = field(default_factory=datetime.now)
      last_updated: datetime = field(default_factory=datetime.now)
      interaction_count: int = 0
      synthesis_version: int = 1

      def compress_for_injection(self, max_tokens: int = 800) -> str:
          """Generate situated context for agent initialization."""
          sections = []

          if self.communication_style:
              sections.append(f"COMMUNICATION: {self.communication_style}")

          if self.goals:
              goals_str = "; ".join(self.goals[-3:])
              sections.append(f"CURRENT GOALS: {goals_str}")

          if self.preferences:
              prefs_items = list(self.preferences.items())[-5:]
              prefs_str = ", ".join(f"{k}: {v}" for k, v in prefs_items)
              sections.append(f"PREFERENCES: {prefs_str}")

          if self.projects:
              projects_items = list(self.projects.items())[-3:]
              projects_str = "; ".join(f"{k}: {v}" for k, v in projects_items)
              sections.append(f"ACTIVE PROJECTS: {projects_str}")

          if self.expertise_areas:
              expertise_str = ", ".join(self.expertise_areas[-5:])
              sections.append(f"EXPERTISE: {expertise_str}")

          if self.constraints:
              constraints_str = "; ".join(self.constraints[-3:])
              sections.append(f"CONSTRAINTS: {constraints_str}")

          result = "\n".join(sections)
          return result[:max_tokens] if len(result) > max_tokens else result

      def update_from_interaction(self, interaction_insights: Dict[str, Any]) -> None:
          """Update profile from interaction insights."""
          self.interaction_count += 1
          self.last_updated = datetime.now()

          # Update preferences
          if "preferences" in interaction_insights:
              self.preferences.update(interaction_insights["preferences"])

          # Add new goals (bounded)
          if "goals" in interaction_insights:
              for goal in interaction_insights["goals"]:
                  if goal not in self.goals:
                      self.goals.append(goal)
              if len(self.goals) > 10:
                  self.goals = self.goals[-10:]

          # Update expertise areas
          if "expertise" in interaction_insights:
              for area in interaction_insights["expertise"]:
                  if area not in self.expertise_areas:
                      self.expertise_areas.append(area)
              if len(self.expertise_areas) > 15:
                  self.expertise_areas = self.expertise_areas[-15:]

          # Update communication style
          if "communication_style" in interaction_insights:
              self.communication_style = interaction_insights["communication_style"]

          # Update project context
          if "project_context" in interaction_insights:
              self.projects.update(interaction_insights["project_context"])
              if len(self.projects) > 10:
                  # Keep most recent projects
                  items = list(self.projects.items())[-10:]
                  self.projects = dict(items)

          # Track success/failure patterns
          if "success_pattern" in interaction_insights:
              pattern = interaction_insights["success_pattern"]
              if pattern and pattern not in self.success_patterns:
                  self.success_patterns.append(pattern)
                  if len(self.success_patterns) > 5:
                      self.success_patterns = self.success_patterns[-5:]

          if "failure_pattern" in interaction_insights:
              pattern = interaction_insights["failure_pattern"]
              if pattern and pattern not in self.failure_patterns:
                  self.failure_patterns.append(pattern)
                  if len(self.failure_patterns) > 5:
                      self.failure_patterns = self.failure_patterns[-5:]

  2. Impression Synthesizer (LLM-Driven Evolution)

  class ImpressionSynthesizer:
      """LLM-driven user understanding synthesis."""

      def __init__(self, llm, store=None):
          self.llm = llm
          self.store = store
          self.synthesis_threshold = 3  # Synthesize every N interactions

      async def update_impression(
          self, 
          user_id: str, 
          interaction_data: Dict[str, Any]
      ) -> UserProfile:
          """Update user impression from interaction."""

          # Load existing profile
          profile = await self._load_profile(user_id)

          # Extract insights from interaction
          insights = await self._extract_insights(interaction_data)

          # Update profile with insights
          if insights:
              profile.update_from_interaction(insights)

          # Synthesize if threshold reached
          if profile.interaction_count % self.synthesis_threshold == 0:
              profile = await self._synthesize_profile(profile, interaction_data)

          # Save updated profile
          if self.store:
              await self._save_profile(profile)

          return profile

      async def _extract_insights(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
          """Extract insights from single interaction."""

          query = interaction_data.get("query", "")
          response = interaction_data.get("response", "")
          success = interaction_data.get("success", True)

          prompt = f"""Extract user insights from this interaction:

  User Query: {query}
  Agent Response: {response}
  Success: {success}

  Extract insights about:
  - User goals and preferences
  - Technical expertise level  
  - Communication preferences
  - Project context
  - Success/failure patterns

  Return JSON:
  {{
      "preferences": {{"key": "value"}},
      "goals": ["goal1", "goal2"],
      "expertise": ["area1", "area2"],
      "communication_style": "concise|detailed|technical",
      "project_context": {{"project_name": "description"}},
      "success_pattern": "what worked",
      "failure_pattern": "what didn't work"
  }}"""

          result = await self.llm.run([{"role": "user", "content": prompt}])
          if result.success:
              from cogency.utils import parse_json
              parsed = parse_json(result.data)
              return parsed.data if parsed.success else {}
          return {}

      async def _synthesize_profile(
          self, 
          profile: UserProfile, 
          recent_interaction: Dict[str, Any]
      ) -> UserProfile:
          """LLM-driven profile synthesis."""

          current_context = profile.compress_for_injection()

          prompt = f"""Synthesize evolved user profile:

  CURRENT PROFILE:
  {current_context}

  RECENT INTERACTION:
  Query: {recent_interaction.get('query', '')}
  Success: {recent_interaction.get('success', True)}

  Create refined profile that:
  - Consolidates understanding over time
  - Prioritizes recent patterns
  - Eliminates contradictions
  - Builds coherent user model

  Return JSON with updated fields:
  {{
      "preferences": {{}},
      "goals": [],
      "expertise_areas": [],
      "communication_style": "",
      "projects": {{}},
      "interests": [],
      "constraints": [],
      "success_patterns": [],
      "failure_patterns": []
  }}"""

          result = await self.llm.run([{"role": "user", "content": prompt}])
          if result.success:
              from cogency.utils import parse_json
              parsed = parse_json(result.data)
              if parsed.success:
                  self._apply_synthesis_to_profile(profile, parsed.data)
                  profile.synthesis_version += 1

          return profile

      def _apply_synthesis_to_profile(self, profile: UserProfile, synthesis_data: Dict[str, Any]) -> None:
          """Apply LLM synthesis to profile."""
          for key, value in synthesis_data.items():
              if hasattr(profile, key) and value:
                  setattr(profile, key, value)

      async def _load_profile(self, user_id: str) -> UserProfile:
          """Load or create user profile."""
          if self.store:
              key = f"profile:{user_id}"
              data = await self.store.load(key)
              if data and "state" in data:
                  profile_data = data["state"]
                  # Handle datetime deserialization
                  if "created_at" in profile_data:
                      profile_data["created_at"] = datetime.fromisoformat(profile_data["created_at"])
                  if "last_updated" in profile_data:
                      profile_data["last_updated"] = datetime.fromisoformat(profile_data["last_updated"])
                  return UserProfile(**profile_data)

          return UserProfile(user_id=user_id)

      async def _save_profile(self, profile: UserProfile) -> None:
          """Save profile to storage."""
          if not self.store:
              return

          key = f"profile:{profile.user_id}"

          # Convert to dict for storage
          profile_dict = asdict(profile)
          profile_dict["created_at"] = profile.created_at.isoformat()
          profile_dict["last_updated"] = profile.last_updated.isoformat()

          await self.store.save(key, profile_dict)

  ---
  🔄 PURE FUNCTIONAL CONTEXT GENERATION

  def build_reasoning_prompt(
      state: AgentState,
      tools: List[Any],
      mode: str = None
  ) -> str:
      """Pure function: State → Reasoning Prompt."""
      mode = mode or state.execution.mode

      # Situated memory injection
      user_context = state.get_situated_context()

      # Reasoning context
      reasoning_context = state.reasoning.compress_for_context()

      # Tool registry
      tool_registry = "\n".join(f"- {tool.name}: {tool.description}" for tool in tools)

      # Recent results
      recent_results = state.execution.completed_calls[-3:] if state.execution.completed_calls else []
      results_context = ""
      if recent_results:
          results_parts = []
          for result in recent_results:
              name = result.get("name", "unknown")
              status = "✓" if result.get("success", False) else "✗"
              results_parts.append(f"{status} {name}")
          results_context = f"RECENT RESULTS:\n" + "\n".join(results_parts) + "\n\n"

      # Mode-specific instructions
      if mode == "deep":
          instructions = """DEEP MODE: Structured reasoning required
  - REFLECT: What have I learned? What worked/failed? What gaps remain?
  - ANALYZE: What are the core problems or strategic considerations?  
  - STRATEGIZE: What's my multi-step plan? What tools will I use and why?"""
      else:
          instructions = """FAST MODE: Direct execution
  - Review context above
  - Choose appropriate tools and act efficiently
  - ESCALATE to deep mode if task proves complex"""

      return f"""{user_context}REASONING CONTEXT:
  {reasoning_context}

  {results_context}AVAILABLE TOOLS:
  {tool_registry}

  {instructions}

  Iteration {state.execution.iteration}/{state.execution.max_iterations}

  Respond with JSON:
  {{
      "thinking": "Your reasoning for this step",
      "tool_calls": [
          {{"name": "tool_name", "args": {{"param": "value"}}}}
      ],
      "context_updates": {{
          "goal": "refined goal if needed",
          "strategy": "current approach", 
          "insights": ["new insight if discovered"]
      }},
      "response": "direct response if ready to answer user",
      "switch_mode": "fast|deep"
  }}"""

  def build_conversation_context(state: AgentState) -> List[Dict[str, str]]:
      """Pure function: State → LLM Messages."""
      return [
          {"role": msg["role"], "content": msg["content"]}
          for msg in state.execution.messages
      ]

  ---
  🚀 OPERATIONAL INTEGRATION

  Agent Initialization

  async def initialize_agent_with_memory(
      query: str,
      user_id: str,
      synthesizer: ImpressionSynthesizer
  ) -> AgentState:
      """Initialize agent with situated memory."""

      # Load user profile
      user_profile = await synthesizer._load_profile(user_id)

      # Create agent state with situated context
      state = AgentState(query=query, user_id=user_id, user_profile=user_profile)

      # Add initial message
      state.execution.add_message("user", query)

      return state

  Interaction Completion

  async def finalize_interaction(
      state: AgentState,
      synthesizer: ImpressionSynthesizer
  ) -> None:
      """Update user impression after interaction."""

      interaction_data = {
          "query": state.execution.query,
          "response": state.execution.response,
          "success": bool(state.execution.response),
          "mode_used": state.execution.mode,
          "iterations": state.execution.iteration
      }

      # Update user impression
      updated_profile = await synthesizer.update_impression(
          state.execution.user_id,
          interaction_data
      )

      # Update state for next interaction
      state.user_profile = updated_profile

  ---
  📋 PRODUCTION REQUIREMENTS (Implementation Phase)

  Mandatory Implementation Requirements (ChatGPT's Concerns)

  1. Compression Validation: Implement token counting and intelligent truncation
  2. Tool Result Extraction: Domain-aware parsing with error handling
  3. Error Recovery: Fallback strategies for malformed updates and tool failures
  4. Loop Control: Enhanced continuation logic beyond just pending tool calls
  5. Migration Testing: Comprehensive test coverage and rollback procedures

  Performance Requirements (Gemini's Concerns)

  1. Async Synthesis: Background user impression updates
  2. Storage Optimization: Efficient serialization/deserialization
  3. Memory Bounds: Strict limits on all collections to prevent runaway growth
  4. Validation: Input sanitization and type checking

  ---
  🔒 ARCHITECTURAL GUARANTEES

  What Will NOT Change Beyond v1.0.0:

  1. ✅ Core state separation: ExecutionState vs ReasoningContext vs UserProfile
  2. ✅ Situated memory architecture: User context injection pattern
  3. ✅ Pure functional context generation: No methods in state classes for prompt building
  4. ✅ Structured facts over strings: No return to string-based cognitive fields
  5. ✅ Dictionary-based tool calls: Simple implementation without custom dataclasses

  What MAY Evolve (Implementation Details Only):

  1. 🔧 Compression algorithms: Better context management strategies
  2. 🔧 Tool result parsing: Enhanced extraction and validation logic
  3. 🔧 Error handling: More sophisticated recovery mechanisms
  4. 🔧 Performance optimizations: Storage, serialization, async patterns
  5. 🔧 Validation logic: Enhanced input sanitization and bounds checking

  ---
  🎯 FINAL COMMITMENT

  This specification represents the permanent architectural foundation for Cogency v1.0.0 and all future versions. The council unanimously approves this design as
  the final state architecture.

  No architectural changes will be made beyond v1.0.0. Only implementation optimizations and performance improvements are permitted, preserving the core separation
  of concerns, situated memory innovation, and pure functional patterns.

  Ship with confidence.

  ---
  🔒 SPECIFICATION LOCKED - READY FOR IMPLEMENTATION