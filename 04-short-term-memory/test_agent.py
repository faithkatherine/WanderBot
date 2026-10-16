#!/usr/bin/env python3
"""Quick test script for WanderBot"""
import asyncio
from starter import invoke


class MockContext:
    """Mock context object for testing"""
    def __init__(self):
        self.session_id = "test-session-123"


async def test_conversation():
    """Test multi-turn conversation"""
    context = MockContext()

    # Turn 1: Ask about Rome hotels
    print("\n" + "="*60)
    print("Turn 1: Asking about Rome hotels")
    print("="*60)
    result1 = await invoke({
        "message": "I'm looking for hotels in Rome under $200 per night",
        "actor_id": "test-user"
    }, context)
    print(result1)

    # Turn 2: Ask follow-up (should remember Rome and budget)
    print("\n" + "="*60)
    print("Turn 2: Follow-up question (should remember context)")
    print("="*60)
    result2 = await invoke({
        "message": "Which one has free cancellation?",
        "actor_id": "test-user"
    }, context)
    print(result2)


if __name__ == "__main__":
    asyncio.run(test_conversation())
