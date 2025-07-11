class Agent:
    def __init__(self, name: str):
        self.name = name

    def run(self, task: str) -> str:
        return f"Agent {self.name} is running task: {task}"
