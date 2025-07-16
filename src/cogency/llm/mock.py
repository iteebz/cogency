from cogency.llm.base import BaseLLM

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def __init__(self, response: str = "Mock response", **kwargs):
        super().__init__(**kwargs)
        self.response = response
    
    async def invoke(self, messages, **kwargs):
        return self.response
    
    async def stream(self, messages, yield_interval: float = 0.0, **kwargs):
        for char in self.response:
            yield char