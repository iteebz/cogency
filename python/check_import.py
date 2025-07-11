try:
    from cogency import Agent
    print("Successfully imported Agent from cogency")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError: {e}")
