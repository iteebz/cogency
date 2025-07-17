#!/usr/bin/env python3
"""Benchmark memory recall accuracy and system performance under load."""

import asyncio
import time
import random
import json
from typing import List, Dict, Any
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.memory.core import MemoryType
import pytest
from pathlib import Path


class MemoryBenchmark:
    """Benchmark memory performance and accuracy."""

    def __init__(self, memory_dir: Path):
        self.memory = FilesystemBackend(str(memory_dir))
        self.test_data = []

    async def setup_test_data(self, num_items: int = 1000):
        """Create test dataset with varied content."""
        print(f"📝 Creating {num_items} test memories...")
        
        # Clear existing data
        await self.memory.clear()
        
        # Generate diverse test data
        categories = ["tech", "personal", "work", "health", "finance", "travel", "food", "entertainment"]
        tech_terms = ["python", "javascript", "ai", "machine learning", "docker", "kubernetes", "api", "database"]
        personal_terms = ["adhd", "anxiety", "family", "friends", "hobbies", "goals", "dreams", "experiences"]
        work_terms = ["meetings", "deadlines", "projects", "team", "manager", "salary", "promotion", "skills"]
        
        term_pools = {
            "tech": tech_terms,
            "personal": personal_terms,
            "work": work_terms,
            "health": ["exercise", "diet", "sleep", "stress", "mental health", "doctor", "medication"],
            "finance": ["budget", "savings", "investment", "taxes", "bills", "expenses", "income"],
            "travel": ["vacation", "flights", "hotels", "passport", "visa", "destinations", "culture"],
            "food": ["cooking", "restaurant", "recipe", "diet", "nutrition", "grocery", "cuisine"],
            "entertainment": ["movies", "music", "books", "games", "sports", "concerts", "theater"]
        }
        
        for i in range(num_items):
            category = random.choice(categories)
            terms = term_pools[category]
            
            # Create varied content patterns
            patterns = [
                f"I {random.choice(['love', 'enjoy', 'prefer', 'use', 'work with'])} {random.choice(terms)}",
                f"My experience with {random.choice(terms)} has been {random.choice(['positive', 'challenging', 'rewarding', 'interesting'])}",
                f"I need to {random.choice(['learn', 'improve', 'focus on', 'work on'])} {random.choice(terms)}",
                f"The {random.choice(terms)} {random.choice(['project', 'task', 'goal', 'issue'])} is {random.choice(['important', 'urgent', 'complex', 'simple'])}",
                f"I remember {random.choice(terms)} being {random.choice(['helpful', 'difficult', 'interesting', 'valuable'])}"
            ]
            
            content = random.choice(patterns)
            tags = [category, random.choice(terms)]
            
            # Add some high-confidence items for accuracy testing
            confidence = 1.0 if i % 10 == 0 else random.uniform(0.7, 1.0)
            
            artifact = await self.memory.memorize(
                content=content,
                memory_type=MemoryType.FACT,
                tags=tags
            )
            artifact.confidence_score = confidence
            
            self.test_data.append({
                "content": content,
                "tags": tags,
                "terms": terms,
                "category": category,
                "confidence": confidence,
                "artifact_id": artifact.id
            })
        
        print(f"✅ Created {len(self.test_data)} test memories")

    async def benchmark_recall_accuracy(self, num_queries: int = 100) -> Dict[str, float]:
        """Test recall accuracy with various query patterns."""
        print(f"🎯 Testing recall accuracy with {num_queries} queries...")
        
        accuracy_stats = {
            "exact_matches": 0,
            "partial_matches": 0,
            "category_matches": 0,
            "false_positives": 0,
            "total_queries": num_queries
        }
        
        for i in range(num_queries):
            # Select random test item to query
            test_item = random.choice(self.test_data)
            
            # Generate query patterns
            query_patterns = [
                random.choice(test_item["terms"]),  # Single term
                f"{random.choice(test_item['terms'])} {random.choice(['experience', 'work', 'project'])}",  # Term + context
                test_item["category"],  # Category query
                " ".join(random.sample(test_item["terms"], min(2, len(test_item["terms"]))))  # Multiple terms
            ]
            
            query = random.choice(query_patterns)
            results = await self.memory.recall(query, limit=5)
            
            # Check accuracy
            if results:
                # Check if original item is in results
                result_ids = [r.id for r in results]
                if test_item["artifact_id"] in result_ids:
                    accuracy_stats["exact_matches"] += 1
                elif any(test_item["category"] in r.tags for r in results):
                    accuracy_stats["category_matches"] += 1
                elif any(any(term in r.content.lower() for term in test_item["terms"]) for r in results):
                    accuracy_stats["partial_matches"] += 1
                else:
                    accuracy_stats["false_positives"] += 1
            else:
                accuracy_stats["false_positives"] += 1
        
        # Calculate percentages
        accuracy_stats["exact_match_rate"] = accuracy_stats["exact_matches"] / num_queries * 100
        accuracy_stats["partial_match_rate"] = accuracy_stats["partial_matches"] / num_queries * 100
        accuracy_stats["category_match_rate"] = accuracy_stats["category_matches"] / num_queries * 100
        accuracy_stats["false_positive_rate"] = accuracy_stats["false_positives"] / num_queries * 100
        
        return accuracy_stats

    async def benchmark_recall_speed(self, num_queries: int = 100) -> Dict[str, float]:
        """Test recall speed performance."""
        print(f"⚡ Testing recall speed with {num_queries} queries...")
        
        times = []
        query_terms = ["python", "work", "personal", "ai", "project", "experience", "learning", "development"]
        
        for i in range(num_queries):
            query = random.choice(query_terms)
            
            start_time = time.time()
            results = await self.memory.recall(query, limit=10)
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        return {
            "avg_query_time": sum(times) / len(times),
            "min_query_time": min(times),
            "max_query_time": max(times),
            "total_queries": num_queries,
            "queries_per_second": num_queries / sum(times)
        }

    async def benchmark_concurrent_load(self, concurrent_users: int = 10, queries_per_user: int = 20) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        print(f"🔄 Testing concurrent load: {concurrent_users} users, {queries_per_user} queries each...")
        
        async def simulate_user(user_id: int) -> Dict[str, Any]:
            """Simulate a user making multiple queries."""
            user_times = []
            query_terms = ["python", "work", "ai", "project", "experience", "personal", "tech", "development"]
            
            for _ in range(queries_per_user):
                query = f"{random.choice(query_terms)} {random.choice(['experience', 'work', 'project', 'skill'])}"
                
                start_time = time.time()
                results = await self.memory.recall(query, limit=5)
                end_time = time.time()
                
                user_times.append(end_time - start_time)
            
            return {
                "user_id": user_id,
                "avg_time": sum(user_times) / len(user_times),
                "total_queries": len(user_times),
                "total_time": sum(user_times)
            }
        
        # Run concurrent users
        start_time = time.time()
        user_tasks = [simulate_user(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*user_tasks)
        end_time = time.time()
        
        # Calculate aggregate stats
        total_queries = sum(r["total_queries"] for r in user_results)
        total_time = end_time - start_time
        avg_response_time = sum(r["avg_time"] for r in user_results) / len(user_results)
        
        return {
            "concurrent_users": concurrent_users,
            "queries_per_user": queries_per_user,
            "total_queries": total_queries,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "queries_per_second": total_queries / total_time,
            "user_results": user_results
        }

    async def benchmark_memory_scaling(self, sizes: List[int] = [100, 500, 1000, 2000]) -> Dict[str, Any]:
        """Test how performance scales with memory size."""
        print(f"📈 Testing memory scaling with sizes: {sizes}")
        
        scaling_results = {}
        
        for size in sizes:
            print(f"  Testing with {size} memories...")
            
            # Setup data for this size
            await self.setup_test_data(size)
            
            # Test query performance
            speed_results = await self.benchmark_recall_speed(50)
            
            scaling_results[size] = {
                "memory_size": size,
                "avg_query_time": speed_results["avg_query_time"],
                "queries_per_second": speed_results["queries_per_second"]
            }
        
        return scaling_results


async def run_memory_benchmarks(tmp_memory_dir: Path):
    """Run comprehensive memory benchmarks."""
    benchmark = MemoryBenchmark(tmp_memory_dir)
    
    print("🧠 Memory Performance Benchmarks")
    print("=" * 50)
    
    # Setup test data
    await benchmark.setup_test_data(1000)
    
    # Run benchmarks
    print("\n1. RECALL ACCURACY")
    accuracy_results = await benchmark.benchmark_recall_accuracy(100)
    print(f"   Exact matches: {accuracy_results['exact_match_rate']:.1f}%")
    print(f"   Partial matches: {accuracy_results['partial_match_rate']:.1f}%")
    print(f"   Category matches: {accuracy_results['category_match_rate']:.1f}%")
    print(f"   False positives: {accuracy_results['false_positive_rate']:.1f}%")
    
    print("\n2. RECALL SPEED")
    speed_results = await benchmark.benchmark_recall_speed(100)
    print(f"   Average query time: {speed_results['avg_query_time']*1000:.1f}ms")
    print(f"   Queries per second: {speed_results['queries_per_second']:.1f}")
    print(f"   Min/Max time: {speed_results['min_query_time']*1000:.1f}ms / {speed_results['max_query_time']*1000:.1f}ms")
    
    print("\n3. CONCURRENT LOAD")
    load_results = await benchmark.benchmark_concurrent_load(10, 20)
    print(f"   Total queries: {load_results['total_queries']}")
    print(f"   Average response time: {load_results['avg_response_time']*1000:.1f}ms")
    print(f"   Throughput: {load_results['queries_per_second']:.1f} queries/sec")
    
    print("\n4. MEMORY SCALING")
    scaling_results = await benchmark.benchmark_memory_scaling([100, 500, 1000])
    for size, stats in scaling_results.items():
        print(f"   {size} memories: {stats['avg_query_time']*1000:.1f}ms avg, {stats['queries_per_second']:.1f} q/s")
    
    # Cleanup
    await benchmark.memory.clear()
    
    print("\n✅ Memory benchmarks completed!")
    print("=" * 50)

    # Save results to a diagnostics file
    import os
    diagnostics_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".diagnostics")
    os.makedirs(diagnostics_dir, exist_ok=True)
    with open(os.path.join(diagnostics_dir, "memory_benchmark_results.json"), "w") as f:
        json.dump({
            "accuracy_results": accuracy_results,
            "speed_results": speed_results,
            "load_results": load_results,
            "scaling_results": scaling_results
        }, f, indent=4)
    print(f"📊 Benchmark results saved to {diagnostics_dir}/memory_benchmark_results.json")


if __name__ == "__main__":
    pytest.main([__file__])