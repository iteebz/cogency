#!/usr/bin/env python3
"""ML Pipeline - From raw data to deployed model."""

import asyncio

from cogency import Agent, Files, Search, Shell


async def main():
    print("🤖 ML PIPELINE")
    print("=" * 40)

    data_scientist = Agent("senior_data_scientist", tools=[Files(), Shell(), Search()])

    # End-to-end ML workflow
    await data_scientist.run_async("""
    Build a complete machine learning pipeline for customer churn prediction:
    
    - Research best practices for churn prediction models
    - Generate realistic customer dataset with proper features
    - Create data preprocessing and feature engineering pipeline
    - Implement multiple ML models (LogisticRegression, RandomForest, XGBoost)
    - Add cross-validation and hyperparameter tuning
    - Create model evaluation and comparison framework
    - Build prediction API with FastAPI and model serving
    - Add comprehensive tests and model monitoring
    - Generate performance report with visualizations
    
    Deliver production-ready ML system with proper MLOps practices.
    """)


if __name__ == "__main__":
    asyncio.run(main())
