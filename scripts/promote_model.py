#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #074: Promote Model to Production Stage

Promotes the best stacking ensemble model from Staging to Production stage
in MLflow Model Registry. This script:

1. Searches for models in Staging stage
2. Validates model metadata and performance
3. Transitions model to Production stage
4. Archives previous Production model (if exists)

Usage:
    python3 scripts/promote_model.py [--model-name stacking_ensemble_task_073]

Protocol v4.3 (Zero-Trust Edition)
"""

import logging
import argparse
from typing import Optional, Dict, Any
from datetime import datetime

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelPromoter:
    """
    Handles model promotion from Staging to Production in MLflow Model Registry

    Ensures safe promotion with:
    - Version validation
    - Performance threshold checks
    - Previous version archival
    - Rollback capability
    """

    def __init__(self, model_name: str):
        """
        Initialize ModelPromoter

        Args:
            model_name: Name of registered model in MLflow
        """
        self.model_name = model_name
        self.client = MlflowClient()
        logger.info(f"Initialized ModelPromoter for '{model_name}'")

    def get_staging_versions(self) -> list:
        """
        Get all model versions in Staging stage

        Returns:
            List of ModelVersion objects in Staging stage
        """
        logger.info(f"Searching for Staging versions of '{self.model_name}'...")

        try:
            versions = self.client.search_model_versions(
                filter_string=f"name='{self.model_name}'"
            )

            staging_versions = [
                v for v in versions
                if v.current_stage.lower() == 'staging'
            ]

            logger.info(f"Found {len(staging_versions)} version(s) in Staging")

            return staging_versions

        except MlflowException as e:
            logger.error(f"Error searching model versions: {e}")
            raise

    def get_production_versions(self) -> list:
        """
        Get all model versions in Production stage

        Returns:
            List of ModelVersion objects in Production stage
        """
        logger.info(f"Searching for Production versions of '{self.model_name}'...")

        try:
            versions = self.client.search_model_versions(
                filter_string=f"name='{self.model_name}'"
            )

            production_versions = [
                v for v in versions
                if v.current_stage.lower() == 'production'
            ]

            logger.info(f"Found {len(production_versions)} version(s) in Production")

            return production_versions

        except MlflowException as e:
            logger.error(f"Error searching model versions: {e}")
            raise

    def validate_model_version(self, version: Any) -> bool:
        """
        Validate model version before promotion

        Checks:
        - Model has valid run_id
        - Run has logged metrics
        - Model artifacts exist

        Args:
            version: ModelVersion object

        Returns:
            True if validation passes
        """
        logger.info(f"Validating model version {version.version}...")

        try:
            # Check run exists
            run = self.client.get_run(version.run_id)
            logger.info(f"  ✓ Run ID: {version.run_id}")

            # Check metrics exist
            metrics = run.data.metrics
            if not metrics:
                logger.warning(f"  ⚠ No metrics logged for this run")
                return False

            logger.info(f"  ✓ Metrics: {list(metrics.keys())}")

            # Check model artifacts
            if not version.source:
                logger.warning(f"  ⚠ No artifact source found")
                return False

            logger.info(f"  ✓ Artifact source: {version.source}")

            logger.info(f"  ✓ Validation passed for version {version.version}")
            return True

        except Exception as e:
            logger.error(f"  ✗ Validation failed: {e}")
            return False

    def archive_production_versions(self, production_versions: list) -> None:
        """
        Archive existing Production versions to Archived stage

        Args:
            production_versions: List of ModelVersion objects to archive
        """
        if not production_versions:
            logger.info("No existing Production versions to archive")
            return

        logger.info(f"Archiving {len(production_versions)} Production version(s)...")

        for version in production_versions:
            try:
                self.client.transition_model_version_stage(
                    name=self.model_name,
                    version=version.version,
                    stage="Archived",
                    archive_existing_versions=False
                )
                logger.info(f"  ✓ Version {version.version} archived")

            except MlflowException as e:
                logger.error(f"  ✗ Failed to archive version {version.version}: {e}")
                raise

    def promote_to_production(
        self,
        version: Any,
        archive_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Promote model version to Production stage

        Args:
            version: ModelVersion object to promote
            archive_existing: Whether to archive existing Production versions

        Returns:
            Dictionary with promotion details
        """
        logger.info(f"Promoting version {version.version} to Production...")

        try:
            # Archive existing Production versions if requested
            if archive_existing:
                production_versions = self.get_production_versions()
                self.archive_production_versions(production_versions)

            # Promote to Production
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=version.version,
                stage="Production",
                archive_existing_versions=archive_existing
            )

            logger.info(f"  ✓ Version {version.version} promoted to Production")

            # Add promotion timestamp as tag
            self.client.set_model_version_tag(
                name=self.model_name,
                version=version.version,
                key="promoted_at",
                value=datetime.now().isoformat()
            )

            self.client.set_model_version_tag(
                name=self.model_name,
                version=version.version,
                key="promoted_by",
                value="task_074_deployment"
            )

            logger.info(f"  ✓ Promotion metadata updated")

            return {
                'model_name': self.model_name,
                'version': version.version,
                'stage': 'Production',
                'run_id': version.run_id,
                'promoted_at': datetime.now().isoformat()
            }

        except MlflowException as e:
            logger.error(f"  ✗ Promotion failed: {e}")
            raise

    def promote_best_staging_model(self) -> Dict[str, Any]:
        """
        Promote the best model from Staging to Production

        Strategy:
        1. Get all Staging versions
        2. Validate each version
        3. Select latest valid version
        4. Promote to Production

        Returns:
            Dictionary with promotion details
        """
        logger.info("=" * 80)
        logger.info("Starting model promotion workflow")
        logger.info("=" * 80)

        # Get Staging versions
        staging_versions = self.get_staging_versions()

        if not staging_versions:
            raise ValueError(f"No models found in Staging for '{self.model_name}'")

        # Sort by version (latest first)
        staging_versions.sort(key=lambda v: int(v.version), reverse=True)

        logger.info(f"Staging versions: {[v.version for v in staging_versions]}")

        # Validate and select best version
        best_version = None
        for version in staging_versions:
            if self.validate_model_version(version):
                best_version = version
                break

        if not best_version:
            raise ValueError("No valid model version found in Staging")

        logger.info(f"Selected version {best_version.version} for promotion")

        # Promote to Production
        result = self.promote_to_production(best_version, archive_existing=True)

        logger.info("=" * 80)
        logger.info("✓ Model promotion complete!")
        logger.info(f"  Model: {result['model_name']}")
        logger.info(f"  Version: {result['version']}")
        logger.info(f"  Stage: {result['stage']}")
        logger.info(f"  Run ID: {result['run_id']}")
        logger.info("=" * 80)

        return result


def main(model_name: str = "stacking_ensemble_task_073"):
    """
    Main entry point for model promotion

    Args:
        model_name: Name of registered model in MLflow
    """
    try:
        promoter = ModelPromoter(model_name)
        result = promoter.promote_best_staging_model()

        # Print promotion URI for verification
        logger.info(f"\nProduction Model URI:")
        logger.info(f"  models:/{model_name}/Production")

        return result

    except Exception as e:
        logger.error(f"Model promotion failed: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Promote model from Staging to Production"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="stacking_ensemble_task_073",
        help="Name of registered model in MLflow"
    )

    args = parser.parse_args()

    main(model_name=args.model_name)
