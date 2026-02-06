"""Application settings using Pydantic."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings."""

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")

    # Agent configuration
    intent_confidence_threshold: float = Field(
        default=0.7, description="Minimum confidence for intent routing"
    )

    # Tax calculation parameters (simplified 2024 values)
    minimum_gross_salary: float = Field(
        default=3300.0, description="Minimum gross salary in RON"
    )
    cas_rate: float = Field(default=0.25, description="CAS contribution rate (25%)")
    cass_rate: float = Field(default=0.10, description="CASS contribution rate (10%)")
    rental_tax_rate: float = Field(default=0.10, description="Rental income tax rate (10%)")
    property_tax_rate_short: float = Field(
        default=0.03, description="Property sale tax rate for < 3 years ownership (3%)"
    )
    property_tax_rate_long: float = Field(
        default=0.01, description="Property sale tax rate for >= 3 years ownership (1%)"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
