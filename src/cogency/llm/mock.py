from cogency.llm.base import BaseLLM

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def __init__(self, response: str = "Mock response", api_keys=None, **kwargs):
        super().__init__(provider_name="mock", api_keys=api_keys or "mock_key", **kwargs)
        self.response = response
    
    async def run(self, messages, **kwargs):
        return self.response
    
    async def stream(self, messages, yield_interval: float = 0.0, **kwargs):
        for char in self.response:
            yield char