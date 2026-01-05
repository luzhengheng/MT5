#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Engineering Module for MT5-CRS

This module provides shared feature computation logic used by both
training and inference to prevent training-serving skew.
"""

from .engineering import compute_features, FeatureConfig

__all__ = ['compute_features', 'FeatureConfig']
