from pathlib import Path

import pytest

from cogency.tools.replace import Replace


@pytest.fixture
def setup_files(tmp_path: Path):
    # Create a temporary directory structure for testing
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sub").mkdir()

    # File 1: simple_file.txt
    file1_path = tmp_path / "simple_file.txt"
    file1_path.write_text("Hello World\nHello Python\nHello World")

    # File 2: src/code.py
    file2_path = tmp_path / "src" / "code.py"
    file2_path.write_text('import os\ndef func():\n    print("Hello World")')

    # File 3: src/sub/another.py
    file3_path = tmp_path / "src" / "sub" / "another.py"
    file3_path.write_text('VERSION = "1.0.0"\n# Some comment')

    # File 4: binary_file.bin
    file4_path = tmp_path / "binary_file.bin"
    file4_path.write_bytes(b"\xff\xfe\x00\x01")

    return {
        "root": tmp_path,
        "file1": file1_path,
        "file2": file2_path,
        "file3": file3_path,
        "file4": file4_path,
    }


@pytest.mark.asyncio
async def test_replace_exact_single_file_single_occurrence(setup_files):
    file_path = setup_files["file1"]
    file_path.read_text()

    result = await Replace.execute(
        pattern="simple_file.txt",
        old="Hello Python",
        new="Hello Cogency",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error
    assert "Changed 1 files" in result.outcome
    assert "Made 1 replacements" in result.outcome
    assert "Hello Cogency" in file_path.read_text()
    assert "Hello Python" not in file_path.read_text()
    assert not (file_path.with_suffix(file_path.suffix + ".bak")).exists()


@pytest.mark.asyncio
async def test_replace_exact_multiple_files(setup_files):
    file1_path = setup_files["file1"]
    file2_path = setup_files["file2"]

    result = await Replace.execute(
        pattern="**/*.py",
        old="import os",
        new="import sys",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error
    assert "Changed 1 files" in result.outcome
    assert "Made 1 replacements" in result.outcome
    assert "import sys" in file2_path.read_text()
    assert "import os" not in file2_path.read_text()
    assert "import sys" not in file1_path.read_text()  # Should not change non-py file


@pytest.mark.asyncio
async def test_replace_sandbox_prefix(setup_files):
    file2_path = setup_files["file2"]

    result = await Replace.execute(
        pattern="sandbox/**/*.py",
        old="import os",
        new="import sys",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error
    assert "Changed 1 files" in result.outcome
    assert "Made 1 replacements" in result.outcome
    assert "import sys" in file2_path.read_text()
    assert "import os" not in file2_path.read_text()


@pytest.mark.asyncio
async def test_replace_exact_multiple_occurrences_fails(setup_files):
    file_path = setup_files["file1"]

    result = await Replace.execute(
        pattern="simple_file.txt",
        old="Hello World",
        new="Hi World",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert result.error
    assert "multiple times" in result.outcome
    assert "Hello World" in file_path.read_text()  # Should not be changed


@pytest.mark.asyncio
async def test_replace_exact_not_found(setup_files):
    file_path = setup_files["file1"]

    result = await Replace.execute(
        pattern="simple_file.txt",
        old="NonExistent",
        new="Found",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error  # No error if nothing found, just no changes
    assert "Changed 0 files" in result.outcome
    assert "Made 0 replacements" in result.outcome
    assert "NonExistent" not in file_path.read_text()


@pytest.mark.asyncio
async def test_replace_regex_single_file_multiple_occurrences(setup_files):
    file_path = setup_files["file1"]

    result = await Replace.execute(
        pattern="simple_file.txt",
        old=r"Hello (World|Python)",
        new=r"Hi \1",
        exact=False,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error
    assert "Changed 1 files" in result.outcome
    assert "Made 3 replacements" in result.outcome
    assert "Hi World" in file_path.read_text()
    assert "Hi Python" in file_path.read_text()
    assert "Hello World" not in file_path.read_text()
    assert "Hello Python" not in file_path.read_text()


@pytest.mark.asyncio
async def test_replace_regex_version_update(setup_files):
    file_path = setup_files["file3"]

    result = await Replace.execute(
        pattern="src/sub/another.py",
        old=r"VERSION = \"(\d+\.\d+\.\d+)\"",
        new='VERSION = "2.0.0"',
        exact=False,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error
    assert "Changed 1 files" in result.outcome
    assert "Made 1 replacements" in result.outcome
    assert 'VERSION = "2.0.0"' in file_path.read_text()
    assert 'VERSION = "1.0.0"' not in file_path.read_text()


@pytest.mark.asyncio
async def test_replace_invalid_regex(setup_files):
    file_path = setup_files["file1"]

    result = await Replace.execute(
        pattern="simple_file.txt",
        old="[",  # Invalid regex
        new="test",
        exact=False,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert result.error
    assert "Invalid regex pattern" in result.outcome
    assert "Hello World" in file_path.read_text()  # Should not be changed


@pytest.mark.asyncio
async def test_replace_no_files_matched(setup_files):
    result = await Replace.execute(
        pattern="non_existent_file.txt",
        old="test",
        new="test",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert result.error
    assert "No files matched" in result.outcome


@pytest.mark.asyncio
async def test_replace_binary_file_skipped(setup_files):
    file_path = setup_files["file4"]
    original_content = file_path.read_bytes()

    result = await Replace.execute(
        pattern="binary_file.bin",
        old="\x00",
        new="\xff",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error
    assert "Changed 0 files" in result.outcome
    assert "Made 0 replacements" in result.outcome
    assert file_path.read_bytes() == original_content  # Should not be changed


@pytest.mark.asyncio
async def test_replace_file_count_limit(setup_files):
    # Create more than 1000 files
    for i in range(1001):
        (setup_files["root"] / f"file_{i}.txt").write_text("test")

    result = await Replace.execute(
        pattern="file_*.txt",
        old="test",
        new="new_test",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert result.error
    assert "Too many files" in result.outcome


@pytest.mark.asyncio
async def test_replace_rollback_on_error(setup_files):
    file1_path = setup_files["file1"]
    file2_path = setup_files["file2"]
    original_content_file1 = file1_path.read_text()
    original_content_file2 = file2_path.read_text()

    # This will cause an error due to multiple occurrences in file1
    result = await Replace.execute(
        pattern="**/*.txt",
        old="Hello World",
        new="Hi World",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert result.error
    assert "multiple times" in result.outcome
    # Verify that file2 was not changed (rollback)
    assert file1_path.read_text() == original_content_file1
    assert file2_path.read_text() == original_content_file2


@pytest.mark.asyncio
async def test_replace_empty_old_string(setup_files):
    result = await Replace.execute(
        pattern="simple_file.txt",
        old="",
        new="new",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )
    assert result.error
    assert "cannot be empty" in result.outcome


@pytest.mark.asyncio
async def test_replace_empty_pattern(setup_files):
    result = await Replace.execute(
        pattern="",
        old="old",
        new="new",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )
    assert result.error
    assert "cannot be empty" in result.outcome


@pytest.mark.asyncio
async def test_replace_describe_method():
    description = Replace.describe({"pattern": "*.txt", "old": "foo", "new": "bar", "exact": True})
    assert "replace(" in description
    assert "pattern=*.txt" in description
    assert "old=foo" in description

    description = Replace.describe(
        {"pattern": "*.py", "old": "func", "new": "method", "exact": False}
    )
    assert "replace(" in description
    assert "pattern=*.py" in description


@pytest.mark.asyncio
async def test_replace_returns_diff_content(setup_files):
    setup_files["file2"]

    result = await Replace.execute(
        pattern="src/code.py",
        old="import os",
        new="import sys",
        exact=True,
        sandbox_dir=str(setup_files["root"]),
        access="sandbox",
    )

    assert not result.error
    assert result.content is not None
    assert "--- " in result.content
    assert "+++ " in result.content
    assert "-import os" in result.content
    assert "+import sys" in result.content
