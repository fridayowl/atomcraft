#!/usr/bin/env python3
"""Retrain ML models from database data."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.core.trainer import train_and_save_models
print("Retraining models from database...")
train_and_save_models(force_retrain=True)
print("Done.")
