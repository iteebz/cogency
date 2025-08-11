#!/usr/bin/env python3
"""Autonomous Coder - From idea to working app in one command."""

import asyncio

from cogency import Agent, Files, Shell


async def main():
    print("🚀 AUTONOMOUS CODER")
    print("=" * 40)

    coder = Agent("senior_engineer", tools=[Files(), Shell()])

    # Single command → complete application
    await coder.run_async("""
    Build a production-ready task management API:

    - FastAPI with async endpoints
    - SQLAlchemy models with proper relationships
    - CRUD operations for users and tasks
    - JWT authentication and middleware
    - Comprehensive test suite with pytest
    - Docker containerization
    - Run tests to verify everything works

    Create a complete, deployable application.
    """)


if __name__ == "__main__":
    asyncio.run(main())
