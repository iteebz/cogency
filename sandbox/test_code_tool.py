import asyncio
import os
from cogency.tools.code import Code

async def main():
    code_tool = Code()

    # Test 1: Create a file
    create_code = """
with open('test_file_from_code.txt', 'w') as f:
    f.write('Hello from isolated code tool!')
print('File created.')
"""
    print("\n--- Testing file creation ---")
    result_create = await code_tool.run(code=create_code, language='python')
    print(f"Result: {result_create}")

    # Test 2: Read the file
    read_code = """
with open('test_file_from_code.txt', 'r') as f:
    content = f.read()
print(f'File content: {content}')
"""
    print("\n--- Testing file reading ---")
    result_read = await code_tool.run(code=read_code, language='python')
    print(f"Result: {result_read}")

    # Clean up: remove the created file
    if os.path.exists('test_file_from_code.txt'):
        os.remove('test_file_from_code.txt')
        print("\nCleaned up test_file_from_code.txt")

if __name__ == "__main__":
    asyncio.run(main())

