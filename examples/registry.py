from cogency.tools import build_registry, get_tools

registry = build_registry(tools=get_tools(), lite=True)
print(registry)

print("===")
registry = build_registry(tools=get_tools(), lite=False)
print(registry)
