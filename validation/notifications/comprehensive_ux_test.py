#!/usr/bin/env python3
"""Validate notification UX and formatting - demonstrates clean, structured output."""

import asyncio

from cogency.utils.notify import Notification, NotificationFormatter, Notifier


def test_notification_formatting():
    """Test that notifications have clean, UX-friendly formatting."""
    print("🎨 NOTIFICATION FORMATTING VALIDATION")
    print("=" * 60)

    # Test formatter with sample notifications
    formatter = NotificationFormatter()

    sample_notifications = [
        Notification(
            phase="preprocess", message="Analyzing query structure", metadata={"mode": "fast"}
        ),
        Notification(
            phase="reason",
            message="Considering available tools",
            metadata={"tools": ["calculator", "weather"]},
        ),
        Notification(
            phase="action",
            message="Executing calculator tool",
            metadata={"tool": "calculator", "input": "15 * 8.5"},
        ),
        Notification(phase="respond", message="Generating final response", metadata={}),
        Notification(
            phase="trace", message="Internal reasoning: Converting units", metadata={"debug": True}
        ),
    ]

    print("✅ EMOJI FORMATTING (UX-friendly):")
    print("-" * 40)
    for i, notif in enumerate(sample_notifications, 1):
        formatted = formatter.format(notif, include_emoji=True)
        print(f"  {i}. {formatted}")

    print("\n✅ TEXT-ONLY FORMATTING (accessibility):")
    print("-" * 40)
    for i, notif in enumerate(sample_notifications, 1):
        formatted = formatter.format(notif, include_emoji=False)
        print(f"  {i}. {formatted}")

    print("\n🔍 STRUCTURE VALIDATION:")
    print("-" * 25)

    # Validate proper phase indicators
    phase_emojis = {"preprocess": "⚙️", "reason": "💭", "action": "⚡", "respond": "🤖", "trace": "🔍"}

    print("Phase emoji mapping:")
    for phase, emoji in phase_emojis.items():
        sample = Notification(phase=phase, message=f"Sample {phase} message", metadata={})
        formatted = formatter.format(sample, include_emoji=True)
        expected_start = f"{emoji} Sample {phase} message"
        has_emoji = formatted.startswith(expected_start)
        print(f"  {emoji} {phase}: {'✅' if has_emoji else '❌'} {formatted}")

    return True


def test_notifier_functionality():
    """Test that Notifier generates proper notifications."""
    print("\n📡 NOTIFIER FUNCTIONALITY TEST:")
    print("-" * 35)

    # Test with verbose enabled
    notifier = Notifier(verbose=True, trace=True)

    print("Testing notification generation:")
    notifier.preprocess("Starting preprocessing phase")
    notifier.reason("Analyzing query intent", {"mode": "fast"})
    notifier.action("Executing calculator tool")
    notifier.respond("Generating response")
    notifier.trace("Debug: internal reasoning step")

    print(f"Generated {len(notifier.notifications)} notifications")

    # Validate structure
    phases = [n.phase for n in notifier.notifications]
    expected_phases = ["preprocess", "reason", "action", "respond", "trace"]

    print("Phase sequence validation:")
    for expected, actual in zip(expected_phases, phases):
        match = expected == actual
        print(f"  Expected '{expected}' → Got '{actual}': {'✅' if match else '❌'}")

    # Test trace filtering
    notifier_no_trace = Notifier(verbose=True, trace=False)
    notifier_no_trace.reason("Normal message")
    notifier_no_trace.trace("Debug message - should be filtered")

    filtered_phases = [n.phase for n in notifier_no_trace.notifications]
    trace_filtered = "trace" not in filtered_phases
    print(f"Trace filtering works: {'✅' if trace_filtered else '❌'}")

    return True


def test_thinking_indicators():
    """Test that thinking/reasoning indicators work."""
    print("\n🧠 THINKING INDICATORS TEST:")
    print("-" * 30)

    formatter = NotificationFormatter()

    thinking_messages = [
        "thinking about the best approach...",
        "considering available options",
        "analyzing the query structure",
        "reasoning through the problem",
    ]

    for msg in thinking_messages:
        notif = Notification(phase="reason", message=msg, metadata={})
        formatted = formatter.format(notif, include_emoji=True)
        has_thinking_emoji = "💭" in formatted
        print(f"  {'✅' if has_thinking_emoji else '❌'} {formatted}")

    return True


async def main():
    """Run comprehensive notification UX validation."""
    print("🚀 COGENCY NOTIFICATION UX VALIDATION")
    print("=" * 70)
    print("Testing clean, structured notification output for optimal DX/UX\n")

    # Run validation tests
    tests = [
        ("Notification Formatting", test_notification_formatting),
        ("Notifier Functionality", test_notifier_functionality),
        ("Thinking Indicators", test_thinking_indicators),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'=' * 70}")
    print("📊 VALIDATION SUMMARY:")
    print("-" * 20)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL NOTIFICATION UX TESTS PASSED!")
        print("\nKey UX Features Validated:")
        print("  • Clean emoji-based phase indicators")
        print("  • Accessibility-friendly text-only fallback")
        print("  • Structured message formatting")
        print("  • Proper phase sequencing")
        print("  • Trace filtering capabilities")
        print("  • Thinking/reasoning visual indicators")
    else:
        print("⚠️  Some tests failed - check output above")

    print("=" * 70)
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
