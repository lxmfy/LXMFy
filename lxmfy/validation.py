"""Validation module for LXMFy configuration and best practices."""

import logging
from dataclasses import dataclass
from typing import Any

from .storage import JSONStorage

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    messages: list[str]
    severity: str  # 'error', 'warning', or 'info'

class ConfigValidator:
    """Validates bot configuration settings."""

    @staticmethod
    def validate_config(config: Any) -> list[ValidationResult]:
        results = []

        try:
            # Validate name
            if len(getattr(config, 'name', '')) < 3:
                results.append(ValidationResult(
                    False,
                    ["Bot name should be at least 3 characters long"],
                    "error"
                ))

            # Validate announce interval
            announce = getattr(config, 'announce', 0)
            if 0 < announce < 300:  # Allow 0 for disabled
                results.append(ValidationResult(
                    False,
                    ["Announce interval should be at least 300 seconds to avoid network spam"],
                    "warning"
                ))

            # Validate rate limiting
            if getattr(config, 'rate_limit', 0) > 10:
                results.append(ValidationResult(
                    False,
                    ["Rate limit above 10 messages per minute may be too permissive"],
                    "warning"
                ))

            # Validate cooldown
            if getattr(config, 'cooldown', 0) < 30:
                results.append(ValidationResult(
                    False,
                    ["Cooldown period should be at least 30 seconds"],
                    "warning"
                ))

        except Exception as e:
            logger.error("Error during config validation: %s", str(e))
            results.append(ValidationResult(
                False,
                [f"Error validating configuration: {str(e)}"],
                "error"
            ))

        return results

class BestPracticesChecker:
    """Checks for bot implementation best practices."""

    @staticmethod
    def check_bot(bot: Any) -> list[ValidationResult]:
        results = []

        # Check permission system usage
        if not getattr(bot.config, 'permissions_enabled', False):
            results.append(ValidationResult(
                False,
                ["Permission system is disabled. Consider enabling it for better security"],
                "warning"
            ))

        # Check command prefix
        if getattr(bot, 'command_prefix', None) is None:
            results.append(ValidationResult(
                False,
                ["Using no command prefix may cause high processing overhead"],
                "warning"
            ))

        # Check admin configuration
        if not getattr(bot, 'admins', None):
            results.append(ValidationResult(
                False,
                ["No admin users configured. Bot management will be limited"],
                "warning"
            ))

        # Check storage configuration
        if getattr(bot.config, 'storage_type', '') == "json":
            results.append(ValidationResult(
                True,
                ["Consider using SQLite storage for better performance with large datasets"],
                "info"
            ))

        return results

class PerformanceAnalyzer:
    """Analyzes bot configuration for performance optimization opportunities."""

    @staticmethod
    def analyze_bot(bot: Any) -> list[ValidationResult]:
        results = []

        # Check caching settings
        if not hasattr(bot, 'transport') or not hasattr(bot.transport, "cached_links"):
            results.append(ValidationResult(
                False,
                ["Link caching is not enabled. This may impact performance"],
                "warning"
            ))

        # Check queue size
        if hasattr(bot, 'queue') and getattr(bot.queue, 'maxsize', 0) < 10:
            results.append(ValidationResult(
                False,
                ["Consider increasing queue size for better message handling"],
                "info"
            ))

        # Check storage backend
        if hasattr(bot, 'storage') and hasattr(bot.storage, 'backend') and isinstance(bot.storage.backend, JSONStorage):
            # Combined checks: storage exists, backend exists, and it's JSONStorage
            results.append(ValidationResult(
                True,
                ["SQLite backend recommended for better performance with large datasets"],
                "info"
            ))

        return results

def validate_bot(bot: Any) -> dict[str, list[ValidationResult]]:
    """Run all validation checks on a bot instance."""
    try:
        return {
            "config": ConfigValidator.validate_config(bot.config),
            "best_practices": BestPracticesChecker.check_bot(bot),
            "performance": PerformanceAnalyzer.analyze_bot(bot)
        }
    except Exception as e:
        logger.error("Validation error: %s", str(e))
        return {
            "error": [ValidationResult(
                False,
                [f"Error during validation: {str(e)}"],
                "error"
            )]
        }

def format_validation_results(results: dict[str, list[ValidationResult]]) -> str:
    """Format validation results into a readable string."""
    output = []

    for category, checks in results.items():
        output.append(f"\n=== {category.upper()} ===")
        for result in checks:
            prefix = "❌" if not result.valid and result.severity == "error" else \
                    "⚠️" if result.severity == "warning" else "ℹ️"
            for msg in result.messages:
                output.append(f"{prefix} {msg}")

    return "\n".join(output) 