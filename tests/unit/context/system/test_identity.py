"""System identity functionality tests."""

import pytest

from cogency.context.system.identity import (
    build_identity_context,
    get_default_identity,
    get_specialized_identity,
)


@pytest.mark.asyncio
async def test_build_identity_context():
    """Test identity context building."""
    context = await build_identity_context("Test Assistant")
    assert context == "IDENTITY: Test Assistant"


@pytest.mark.asyncio
async def test_build_identity_context_empty():
    """Test identity context with empty identity."""
    context = await build_identity_context("")
    assert context is None


@pytest.mark.asyncio
async def test_build_identity_context_whitespace():
    """Test identity context strips whitespace."""
    context = await build_identity_context("  Test Assistant  ")
    assert context == "IDENTITY: Test Assistant"


def test_get_default_identity():
    """Test default identity retrieval."""
    identity = get_default_identity()
    assert "AI Assistant" in identity
    assert "helpful" in identity.lower()


def test_get_specialized_identity():
    """Test specialized identity generation."""
    coder_identity = get_specialized_identity("coder")
    assert "Software Engineer" in coder_identity
    assert "code" in coder_identity.lower()

    analyst_identity = get_specialized_identity("analyst")
    assert "Data Analyst" in analyst_identity
    assert "analysis" in analyst_identity.lower()


def test_get_specialized_identity_unknown():
    """Test specialized identity with unknown role."""
    identity = get_specialized_identity("unknown_role")
    assert identity == get_default_identity()
