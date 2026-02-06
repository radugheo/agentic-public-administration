"""Tests for the Calculation Agent Service."""

import pytest
from ro_tax_agents.services.calculation_agent import calculation_agent_service
from ro_tax_agents.orchestration.main_graph import get_initial_state


class TestPropertySaleTaxCalculation:
    """Tests for property sale tax calculations."""

    def test_property_tax_3_percent_under_3_years(self):
        """Property owned less than 3 years should have 3% tax."""
        state = get_initial_state("test-session")
        state["shared_context"] = {
            "property_value": 100000,
            "ownership_duration_years": 2,
            "calculation_type": "property_sale_tax",
        }

        result = calculation_agent_service.process(state)

        assert result["shared_context"]["tax_rate"] == 0.03
        assert result["shared_context"]["calculated_tax"] == 3000.0

    def test_property_tax_1_percent_over_3_years(self):
        """Property owned 3+ years should have 1% tax."""
        state = get_initial_state("test-session")
        state["shared_context"] = {
            "property_value": 100000,
            "ownership_duration_years": 5,
            "calculation_type": "property_sale_tax",
        }

        result = calculation_agent_service.process(state)

        assert result["shared_context"]["tax_rate"] == 0.01
        assert result["shared_context"]["calculated_tax"] == 1000.0

    def test_property_tax_exactly_3_years(self):
        """Property owned exactly 3 years should have 1% tax."""
        state = get_initial_state("test-session")
        state["shared_context"] = {
            "property_value": 200000,
            "ownership_duration_years": 3,
            "calculation_type": "property_sale_tax",
        }

        result = calculation_agent_service.process(state)

        assert result["shared_context"]["tax_rate"] == 0.01
        assert result["shared_context"]["calculated_tax"] == 2000.0


class TestPFAContributionsCalculation:
    """Tests for PFA CAS/CASS calculations."""

    def test_pfa_above_both_thresholds(self):
        """Income above both thresholds should pay both CAS and CASS."""
        state = get_initial_state("test-session")
        state["shared_context"] = {
            "annual_income": 150000,
            "calculation_type": "pfa_contributions",
        }

        result = calculation_agent_service.process(state)

        # CAS: 25% of 12 minimum salaries (3300 * 12 * 0.25 = 9900)
        # CASS: 10% of 6 minimum salaries (3300 * 6 * 0.10 = 1980)
        assert result["shared_context"]["cas_amount"] == 9900.0
        assert result["shared_context"]["cass_amount"] == 1980.0
        assert result["shared_context"]["total_contributions"] == 11880.0

    def test_pfa_below_cas_threshold(self):
        """Income below CAS threshold but above CASS should pay only CASS."""
        state = get_initial_state("test-session")
        state["shared_context"] = {
            "annual_income": 25000,  # Below 12 min salaries (39600), above 6 (19800)
            "calculation_type": "pfa_contributions",
        }

        result = calculation_agent_service.process(state)

        assert result["shared_context"]["cas_amount"] == 0.0
        assert result["shared_context"]["cass_amount"] == 1980.0

    def test_pfa_below_both_thresholds(self):
        """Income below both thresholds should pay nothing."""
        state = get_initial_state("test-session")
        state["shared_context"] = {
            "annual_income": 15000,  # Below both thresholds
            "calculation_type": "pfa_contributions",
        }

        result = calculation_agent_service.process(state)

        assert result["shared_context"]["cas_amount"] == 0.0
        assert result["shared_context"]["cass_amount"] == 0.0
        assert result["shared_context"]["total_contributions"] == 0.0


class TestRentalTaxCalculation:
    """Tests for rental income tax calculations."""

    def test_rental_tax_calculation(self):
        """Rental income should be taxed at 10%."""
        state = get_initial_state("test-session")
        state["shared_context"] = {
            "monthly_rent": 500,
            "calculation_type": "rental_income_tax",
        }

        result = calculation_agent_service.process(state)

        # 500 * 12 = 6000 annual, 10% = 600
        assert result["shared_context"]["annual_rent"] == 6000.0
        assert result["shared_context"]["rental_tax"] == 600.0
