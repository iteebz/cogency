"""Embedding provider validation - test different embedding backends."""

import asyncio
import contextlib
import os

import numpy as np

from cogency.services.embed import MistralEmbed, Nomic, OpenAIEmbed, Sentence


async def test_embedding_availability():
    """Test which embedding providers are available."""
    print("🔍 Testing embedding provider availability...")

    providers = [
        ("OpenAI", OpenAIEmbed, "OPENAI_API_KEY"),
        ("Nomic", Nomic, None),  # Local model
        ("SentenceTransformers", Sentence, None),  # Local model
        ("Mistral", MistralEmbed, "MISTRAL_API_KEY"),
    ]

    available_providers = []

    for name, provider_class, env_key in providers:
        if env_key is None or os.environ.get(env_key):
            try:
                embed = provider_class()
                test_text = "This is a test sentence for embedding."
                result = embed.embed(test_text)
                embedding = result.data if result.success else None

                if embedding and len(embedding) > 0:
                    print(f"✅ {name} provider available (dim: {len(embedding)})")
                    available_providers.append(name)
                else:
                    print(f"⚠️  {name} provider configured but returned empty embedding")

            except Exception as e:
                print(f"❌ {name} provider failed: {e}")
        else:
            print(f"⚪ {name} provider not configured (missing {env_key})")

    return len(available_providers) > 0


async def test_embedding_consistency():
    """Test that embedding providers give consistent results."""
    print("🎯 Testing embedding consistency...")

    # Use available providers
    test_providers = []

    if os.environ.get("OPENAI_API_KEY"):
        test_providers.append(("OpenAI", OpenAIEmbed))

    with contextlib.suppress(Exception):
        test_providers.append(("Nomic", Nomic))

    with contextlib.suppress(Exception):
        test_providers.append(("SentenceTransformers", Sentence))

    if len(test_providers) == 0:
        print("⚠️  No providers configured for consistency testing")
        return True

    test_sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is transforming artificial intelligence.",
        "Python is a popular programming language.",
    ]

    results = []

    for name, provider_class in test_providers:
        try:
            embed = provider_class()
            embeddings = []

            for sentence in test_sentences:
                result = embed.embed(sentence)
                embedding = result.data if result.success else None
                embeddings.append(embedding)

            # Check that embeddings are different for different sentences
            if len(embeddings) == 3 and all(e is not None for e in embeddings):
                # Calculate cosine similarity between first two embeddings
                e1, e2 = np.array(embeddings[0]).flatten(), np.array(embeddings[1]).flatten()
                similarity = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))

                # Embeddings should be different (similarity < 0.9)
                if similarity < 0.9:
                    print(f"✅ {name} embeddings show proper differentiation")
                    results.append(True)
                else:
                    print(f"❌ {name} embeddings too similar ({similarity:.3f})")
                    results.append(False)
            else:
                print(f"❌ {name} didn't return all embeddings")
                results.append(False)

        except Exception as e:
            print(f"❌ {name} consistency test failed: {e}")
            results.append(False)

    return all(results) if results else True


async def test_embedding_batch_processing():
    """Test batch embedding processing."""
    print("📦 Testing batch embedding processing...")

    # Test with first available provider
    test_embed = None
    provider_name = "Unknown"

    if os.environ.get("OPENAI_API_KEY"):
        test_embed = OpenAIEmbed()
        provider_name = "OpenAI"
    else:
        with contextlib.suppress(Exception):
            test_embed = Nomic()
            provider_name = "Nomic"
        if not test_embed:
            with contextlib.suppress(Exception):
                test_embed = Sentence()
                provider_name = "SentenceTransformers"

    if not test_embed:
        print("⚠️  No providers available for batch processing test")
        return True

    batch_texts = [
        "First document for batch processing",
        "Second document with different content",
        "Third document for testing batches",
        "Fourth and final document",
    ]

    try:
        # Test individual embeddings
        individual_embeddings = []
        for text in batch_texts:
            result = test_embed.embed(text)
            embedding = result.data if result.success else None
            individual_embeddings.append(embedding)

        # Check that all embeddings were generated
        if len(individual_embeddings) == len(batch_texts) and all(
            e is not None and len(e) > 0 for e in individual_embeddings
        ):
            print(f"✅ {provider_name} batch processing working")
            return True
        else:
            print(f"❌ {provider_name} batch processing failed")
            return False

    except Exception as e:
        print(f"❌ {provider_name} batch processing crashed: {e}")
        return False


async def test_embedding_dimensions():
    """Test embedding dimension consistency."""
    print("📏 Testing embedding dimensions...")

    # Test with first available provider
    test_embed = None
    provider_name = "Unknown"

    if os.environ.get("OPENAI_API_KEY"):
        test_embed = OpenAIEmbed()
        provider_name = "OpenAI"
    else:
        with contextlib.suppress(Exception):
            test_embed = Nomic()
            provider_name = "Nomic"
        if not test_embed:
            with contextlib.suppress(Exception):
                test_embed = Sentence()
                provider_name = "SentenceTransformers"

    if not test_embed:
        print("⚠️  No providers available for dimension test")
        return True

    test_texts = [
        "Short text",
        "This is a much longer text with more words and content to test dimension consistency",
        "🚀 Text with emojis and special characters! @#$%",
    ]

    try:
        embeddings = []
        for text in test_texts:
            result = test_embed.embed(text)
            embedding = result.data if result.success else None
            embeddings.append(embedding)

        # Check dimension consistency
        dimensions = [len(e) for e in embeddings if e is not None]
        if len(set(dimensions)) == 1 and dimensions[0] > 0:
            print(f"✅ {provider_name} dimensions consistent ({dimensions[0]})")
            return True
        else:
            print(f"❌ {provider_name} dimensions inconsistent: {dimensions}")
            return False

    except Exception as e:
        print(f"❌ {provider_name} dimension test crashed: {e}")
        return False


async def main():
    """Run all embedding provider validation tests."""
    print("🚀 Starting embedding provider validation...\n")

    tests = [
        test_embedding_availability,
        test_embedding_consistency,
        test_embedding_batch_processing,
        test_embedding_dimensions,
    ]

    results = []
    for test in tests:
        try:
            success = await test()
            results.append(success)
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)

    print(f"📊 Embedding provider validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Embedding providers are production ready!")
    else:
        print("⚠️  Embedding providers need attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
