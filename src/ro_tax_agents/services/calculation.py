"""Calculation Service - Tax computation."""

from typing import Any
from decimal import Decimal
from langchain_core.messages import AIMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.settings import settings


class CalculationService:
    """Tax computation service.

    This service performs various Romanian tax calculations including:
    - PFA contributions (CAS/CASS)
    - Property sale tax (1%/3%)
    - Rental income tax (10%)
    """

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Perform tax calculations based on context.

        Args:
            state: Current agent state

        Returns:
            State updates with calculation results
        """
        shared_context = state.get("shared_context", {})
        calculation_type = shared_context.get("calculation_type")

        if calculation_type == "property_sale_tax":
            return self._calculate_property_sale_tax(state)
        elif calculation_type == "pfa_contributions":
            return self._calculate_pfa_contributions(state)
        elif calculation_type == "rental_income_tax":
            return self._calculate_rental_tax(state)
        else:
            return {
                "error_message": f"Unknown calculation type: {calculation_type}",
                "workflow_status": "error",
                "messages": [AIMessage(content=f"Nu pot efectua calculul pentru tipul: {calculation_type}")],
            }

    def _calculate_property_sale_tax(self, state: BaseAgentState) -> dict[str, Any]:
        """Calculate property sale tax (1% or 3%).

        Tax rates:
        - 3% if property owned less than 3 years
        - 1% if property owned 3 years or more
        """
        shared_context = state.get("shared_context", {})
        property_value = Decimal(str(shared_context.get("property_value", 0)))
        ownership_years = shared_context.get("ownership_duration_years", 0)

        # Determine tax rate based on ownership duration
        if ownership_years >= 3:
            tax_rate = Decimal(str(settings.property_tax_rate_long))  # 1%
            rate_explanation = "1% (proprietate detinuta >= 3 ani)"
        else:
            tax_rate = Decimal(str(settings.property_tax_rate_short))  # 3%
            rate_explanation = "3% (proprietate detinuta < 3 ani)"

        calculated_tax = property_value * tax_rate

        message = (
            f"Calcul impozit vanzare proprietate:\n"
            f"  Valoare proprietate: {property_value:,.2f} RON\n"
            f"  Durata detinere: {ownership_years} ani\n"
            f"  Cota aplicabila: {rate_explanation}\n"
            f"  Impozit datorat: {calculated_tax:,.2f} RON"
        )

        return {
            "shared_context": {
                **shared_context,
                "tax_rate": float(tax_rate),
                "calculated_tax": float(calculated_tax),
                "calculation_details": {
                    "property_value": float(property_value),
                    "ownership_years": ownership_years,
                    "rate_explanation": rate_explanation,
                },
            },
            "messages": [AIMessage(content=message)],
        }

    def _calculate_pfa_contributions(self, state: BaseAgentState) -> dict[str, Any]:
        """Calculate CAS/CASS contributions for PFA.

        CAS (pension): 25% of minimum 12 salaries if income >= 12 minimum salaries
        CASS (health): 10% of minimum 6 salaries if income >= 6 minimum salaries
        """
        shared_context = state.get("shared_context", {})
        annual_income = Decimal(str(shared_context.get("annual_income", 0)))

        # Get thresholds from settings
        minimum_salary = Decimal(str(settings.minimum_gross_salary))
        cas_rate = Decimal(str(settings.cas_rate))
        cass_rate = Decimal(str(settings.cass_rate))

        cas_threshold = minimum_salary * 12  # 12 minimum salaries
        cass_threshold = minimum_salary * 6  # 6 minimum salaries

        # Calculate CAS
        cas_amount = Decimal("0")
        cas_explanation = "Nu se datoreaza (venit sub pragul de 12 salarii minime)"
        if annual_income >= cas_threshold:
            cas_base = cas_threshold  # CAS is calculated on the threshold, not actual income
            cas_amount = cas_base * cas_rate
            cas_explanation = f"25% din {cas_threshold:,.2f} RON (12 x salariul minim)"

        # Calculate CASS
        cass_amount = Decimal("0")
        cass_explanation = "Nu se datoreaza (venit sub pragul de 6 salarii minime)"
        if annual_income >= cass_threshold:
            cass_base = cass_threshold  # CASS is calculated on the threshold
            cass_amount = cass_base * cass_rate
            cass_explanation = f"10% din {cass_threshold:,.2f} RON (6 x salariul minim)"

        total_contributions = cas_amount + cass_amount

        message = (
            f"Calcul contributii PFA pentru venitul anual de {annual_income:,.2f} RON:\n\n"
            f"Salariul minim brut: {minimum_salary:,.2f} RON\n\n"
            f"CAS (contributie pensii):\n"
            f"  Prag: {cas_threshold:,.2f} RON (12 salarii minime)\n"
            f"  {cas_explanation}\n"
            f"  CAS datorat: {cas_amount:,.2f} RON\n\n"
            f"CASS (contributie sanatate):\n"
            f"  Prag: {cass_threshold:,.2f} RON (6 salarii minime)\n"
            f"  {cass_explanation}\n"
            f"  CASS datorat: {cass_amount:,.2f} RON\n\n"
            f"TOTAL contributii: {total_contributions:,.2f} RON"
        )

        return {
            "shared_context": {
                **shared_context,
                "cas_amount": float(cas_amount),
                "cass_amount": float(cass_amount),
                "total_contributions": float(total_contributions),
                "calculation_details": {
                    "minimum_salary": float(minimum_salary),
                    "cas_threshold": float(cas_threshold),
                    "cass_threshold": float(cass_threshold),
                    "cas_explanation": cas_explanation,
                    "cass_explanation": cass_explanation,
                },
            },
            "messages": [AIMessage(content=message)],
        }

    def _calculate_rental_tax(self, state: BaseAgentState) -> dict[str, Any]:
        """Calculate rental income tax (10% flat tax)."""
        shared_context = state.get("shared_context", {})
        monthly_rent = Decimal(str(shared_context.get("monthly_rent", 0)))

        # 10% flat tax on rental income
        rental_tax_rate = Decimal(str(settings.rental_tax_rate))
        annual_rent = monthly_rent * 12
        tax_amount = annual_rent * rental_tax_rate

        message = (
            f"Calcul impozit venit din chirii:\n"
            f"  Chirie lunara: {monthly_rent:,.2f} RON\n"
            f"  Venit anual: {annual_rent:,.2f} RON\n"
            f"  Cota impozit: 10%\n"
            f"  Impozit anual datorat: {tax_amount:,.2f} RON"
        )

        return {
            "shared_context": {
                **shared_context,
                "annual_rent": float(annual_rent),
                "rental_tax": float(tax_amount),
                "rental_tax_rate": float(rental_tax_rate),
            },
            "messages": [AIMessage(content=message)],
        }

    def __call__(self, state: BaseAgentState) -> dict[str, Any]:
        """Make the service callable as a LangGraph node."""
        return self.process(state)


# Singleton instance
calculation_service = CalculationService()
