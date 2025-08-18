"""
farm_debt_manager.py

Simulates farm cashflow and loan repayment restructuring options:
- baseline amortized EMI
- bullet repayment at harvest
- extend tenure (lower EMI)
- partial repayment at harvest + amortize remaining

Assumptions are configurable (harvest months, number of harvests, marketing deductions).
This cleaned up version avoids NumPy arrays in outputs and ensures all returned values are
native Python types (float/int/bool) to be JSON-serializable.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Tuple
import math
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))

from utils.utils import prettify_details

@dataclass
class FarmInputs:
    area_ha: float
    yield_q_per_ha: float
    price_per_q: float
    input_cost: float               # total inputs for the season (₹)
    insurance: float                # insurance premium (₹)
    household_monthly: float        # household expense per month (₹)
    off_farm_monthly: float         # off-farm income per month (₹)
    loan_principal: float           # loan principal (₹)
    annual_interest_rate: float     # annual interest percent, e.g., 7 for 7%
    loan_tenure_months: int         # tenure for EMI simulation (months)
    marketing_deduction_pct: float = 0.02  # fraction of revenue lost to market (default 2%)
    harvest_months: List[int] = field(default_factory=lambda: [4])  # months (1-12) when harvests bring income


class FarmDebtManager:
    def __init__(self, inputs: FarmInputs):
        # Ensure inputs are plain Python scalars to avoid accidental array operations
        self.i = FarmInputs(
            area_ha=float(inputs.area_ha),
            yield_q_per_ha=float(inputs.yield_q_per_ha),
            price_per_q=float(inputs.price_per_q),
            input_cost=float(inputs.input_cost),
            insurance=float(inputs.insurance),
            household_monthly=float(inputs.household_monthly),
            off_farm_monthly=float(inputs.off_farm_monthly),
            loan_principal=float(inputs.loan_principal),
            annual_interest_rate=float(inputs.annual_interest_rate),
            loan_tenure_months=int(inputs.loan_tenure_months),
            marketing_deduction_pct=float(inputs.marketing_deduction_pct),
            harvest_months=list(inputs.harvest_months) if inputs.harvest_months is not None else [4]
        )

    # ---------- utility ----------
    def _monthly_rate(self) -> float:
        return self.i.annual_interest_rate / 12.0 / 100.0

    def _emi(self, principal: float, tenure_months: int, annual_rate: float) -> float:
        principal = float(principal)
        tenure_months = int(tenure_months)
        if principal <= 0 or tenure_months <= 0:
            return 0.0
        r = annual_rate / 12.0 / 100.0
        if r == 0:
            return principal / tenure_months
        # standard EMI formula
        emi = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
        return float(emi)

    # ---------- core calculations ----------
    def compute_revenue(self) -> Tuple[float, float]:
        """Return (gross_revenue, net_revenue_after_marketing_deduction) as floats."""
        area_ha = float(self.i.area_ha)
        yield_q_per_ha = float(self.i.yield_q_per_ha)
        price_per_q = float(self.i.price_per_q)
        gross = area_ha * yield_q_per_ha * price_per_q
        net = gross * (1.0 - float(self.i.marketing_deduction_pct))
        return float(gross), float(net)

    def baseline(self) -> Dict:
        """Compute baseline yearly cash figures and baseline monthly EMI schedule."""
        gross, net_rev = self.compute_revenue()
        net_farm_income = net_rev - float(self.i.input_cost) - float(self.i.insurance)
        seasonal_offfarm = float(self.i.off_farm_monthly) * 6.0
        total_available = net_farm_income + seasonal_offfarm
        seasonal_household = float(self.i.household_monthly) * 6.0

        emi_monthly = self._emi(self.i.loan_principal, self.i.loan_tenure_months, self.i.annual_interest_rate)
        seasonal_loan_outflow = emi_monthly * 6.0

        surplus_before_debt = total_available - seasonal_household
        surplus_after_loan = surplus_before_debt - seasonal_loan_outflow

        seasonal_loan_outflow_val = float(seasonal_loan_outflow)
        numerator = float(surplus_before_debt)
        denom = seasonal_loan_outflow_val if seasonal_loan_outflow_val != 0 else math.inf
        debt_sustainability_index = round((numerator / denom) if denom != 0 and denom != math.inf else math.inf, 3)

        return {
            # "Predicted Price": round(float(self.i.price_per_q), 2),
            # "Predicted Yield": round(float(self.i.yield_q_per_ha), 2),
            "gross_revenue": round(float(gross), 2),
            "net_revenue_after_marketing": round(float(net_rev), 2),
            "net_farm_income": round(float(net_farm_income), 2),
            "seasonal_offfarm_income": round(float(seasonal_offfarm), 2),
            "total_available": round(float(total_available), 2),
            "seasonal_household_need": round(float(seasonal_household), 2),
            "emi_monthly_baseline": round(float(emi_monthly), 2),
            "seasonal_loan_outflow_baseline": round(float(seasonal_loan_outflow_val), 2),
            "surplus_before_loan": round(float(surplus_before_debt), 2),
            "surplus_after_loan": round(float(surplus_after_loan), 2),
            "debt_sustainability_index": debt_sustainability_index
        }

    # ---------- restructuring scenarios ----------
    def bullet_repayment_at_harvest(self, harvest_index: int = 0) -> Dict:
        """
        Entire principal + accrued interest for months_until_harvest is paid once at harvest.
        months_until_harvest: compute as months difference from start (month 1) to harvest_month.
        For simplicity assume season starts at month 1 and harvest_month in inputs.harvest_months list.
        """
        # months until first scheduled harvest:
        if len(self.i.harvest_months) == 0:
            months_until_harvest = 6
        else:
            harvest_m = int(self.i.harvest_months[min(harvest_index, len(self.i.harvest_months)-1)])
            months_until_harvest = harvest_m if harvest_m >= 1 else 6

        # interest accrued till harvest (simple interest)
        accrued_interest = float(self.i.loan_principal) * (float(self.i.annual_interest_rate) / 100.0) * (months_until_harvest / 12.0)
        payout_at_harvest = float(self.i.loan_principal) + accrued_interest

        # prepare yearly flows: assume harvest provides net_farm_income at that harvest
        _, net_rev = self.compute_revenue()
        net_farm_income = float(net_rev) - float(self.i.input_cost) - float(self.i.insurance)

        seasonal_offfarm = float(self.i.off_farm_monthly) * 6.0
        seasonal_household = float(self.i.household_monthly) * 6.0

        total_available = net_farm_income + seasonal_offfarm
        leftover_after_bullet = total_available - payout_at_harvest - seasonal_household

        return {
            "months_until_harvest": int(months_until_harvest),
            "accrued_interest_till_harvest": round(float(accrued_interest), 2),
            "payout_at_harvest": round(float(payout_at_harvest), 2),
            "total_available": round(float(total_available), 2),
            "leftover_after_bullet": round(float(leftover_after_bullet), 2),
            "is_sufficient": bool(float(leftover_after_bullet) >= 0)
        }

    def extend_tenure_option(self, new_tenure_months: int) -> Dict:
        """Simulate EMI if tenure extended to new_tenure_months (same principal & rate)."""
        new_tenure_months = int(new_tenure_months)
        emi_new = self._emi(self.i.loan_principal, new_tenure_months, self.i.annual_interest_rate)
        seasonal_loan_new = emi_new * 6.0
        b = self.baseline()
        surplus_before_loan = float(b["surplus_before_loan"])
        surplus_after_newloan = surplus_before_loan - float(seasonal_loan_new)
        return {
            "new_tenure_months": new_tenure_months,
            "emi_monthly_new": round(float(emi_new), 2),
            "seasonal_loan_outflow_new": round(float(seasonal_loan_new), 2),
            "surplus_after_newloan": round(float(surplus_after_newloan), 2),
            "is_sufficient": bool(float(surplus_after_newloan) >= 0)
        }

    def partial_repay_then_amortize(self, repay_at_harvest: float, amortize_tenure_months: int) -> Dict:
        """
        Simulate paying 'repay_at_harvest' immediately at harvest (principal reduction).
        Remaining principal = loan_principal - repay_at_harvest.
        Then amortize remaining principal over amortize_tenure_months with same annual rate.
        """
        repay_at_harvest = float(repay_at_harvest)
        amortize_tenure_months = int(amortize_tenure_months)

        principal_remaining = max(0.0, float(self.i.loan_principal) - repay_at_harvest)
        emi_after = self._emi(principal_remaining, amortize_tenure_months, self.i.annual_interest_rate)
        seasonal_loan_after = emi_after * 6.0

        # compute if repay_at_harvest itself is feasible from harvest cash
        _, net_rev = self.compute_revenue()
        net_farm_income = float(net_rev) - float(self.i.input_cost) - float(self.i.insurance)
        harvest_cash = float(net_farm_income)  # assume harvest provides net_farm_income at harvest

        # Annual totals:
        total_available = net_farm_income + (float(self.i.off_farm_monthly) * 6.0)
        seasonal_household = float(self.i.household_monthly) * 6.0
        surplus_before_loan = total_available - seasonal_household

        surplus_after_partial = surplus_before_loan - seasonal_loan_after  # repay_at_harvest assumed covered from harvest_cash
        harvest_can_afford = bool(harvest_cash >= repay_at_harvest)

        return {
            "repay_at_harvest": round(float(repay_at_harvest), 2),
            "principal_remaining": round(float(principal_remaining), 2),
            "emi_after_amortize_monthly": round(float(emi_after), 2),
            "seasonal_loan_after": round(float(seasonal_loan_after), 2),
            "surplus_after_partial_amortize": round(float(surplus_after_partial), 2),
            "harvest_cash": round(float(harvest_cash), 2),
            "harvest_can_afford_partial": harvest_can_afford,
            "is_sufficient": bool(float(surplus_after_partial) >= 0)
        }

    # ---------- recommendation engine ----------
    def recommend(self) -> Dict:
        """
        Run scenario simulations and recommend feasible restructuring(s).
        Strategy:
          - check baseline (EMI)
          - apply simple repayment heuristics and produce ranked feasible options
        """
        results = {}
        baseline = self.baseline()
        results['baseline'] = baseline

        # 1) bullet
        bullet = self.bullet_repayment_at_harvest()
        results['bullet'] = bullet

        # 2) extend tenure candidates
        extend_candidates = [
            self.extend_tenure_option(6 + self.i.loan_tenure_months),  # extend by +6m
            self.extend_tenure_option(24),
            self.extend_tenure_option(36)
        ]
        results['extend'] = extend_candidates

        # 3) partial repay scenarios
        partials = []
        for pct in [0.25, 0.5]:
            repay_amt = round(float(self.i.loan_principal) * pct, 2)
            for tenure in [12, 24, 36]:
                partials.append((pct, tenure, self.partial_repay_then_amortize(repay_amt, tenure)))
        results['partials'] = partials

        # ---------- Apply repayment conditions ----------
        recs = []
        surplus_after_loan = float(baseline["surplus_after_loan"])
        surplus_before_loan = float(baseline["surplus_before_loan"])
        emi_baseline = float(baseline["emi_monthly_baseline"])

        # If baseline already sufficient
        if surplus_after_loan >= 0:
            recs.append({
                "option": "full_repay_at_harvest",
                "score_surplus": round(float(surplus_after_loan), 2),
                "details": {
                    "message": "✅ You can fully repay loan at harvest from surplus."
                }
            })

        # If close, suggest household cut
        elif surplus_before_loan >= 0.8 * (emi_baseline * 6.0):
            cut_needed = (emi_baseline * 6.0 - surplus_before_loan)
            recs.append({
                "option": "reducing_household_expense",
                "score_surplus": round(float(surplus_before_loan), 2),
                "details": {
                    "message": f"⚠️ Surplus is slightly short. Reduce household expense by ~₹{cut_needed:.0f}/season "
                               f"(~₹{cut_needed/6.0:.0f}/mo) to stay on EMI schedule."
                }
            })

        else:
            # ---------- Add other scenario comparisons ----------
            feasible = []

            # helper to format amounts safely
            def _fmt_amt(x):
                try:
                    if x is None:
                        return "N/A"
                    x = float(x)
                    if math.isinf(x) or math.isnan(x):
                        return "N/A"
                    # format with commas and two decimals
                    return f"₹{x:,.2f}"
                except Exception:
                    return str(x)

            # bullet option (if feasible)
            if bool(bullet.get("is_sufficient", False)):
                leftover = bullet.get("leftover_after_bullet")
                leftover_fmt = _fmt_amt(leftover)
                if leftover is not None and leftover_fmt != "N/A":
                    msg = (
                        f"Repay the full outstanding loan at harvest using the seasonal surplus. "
                        f"After repayment you will have approximately {leftover_fmt} remaining."
                    )
                else:
                    msg = (
                        "Repay the full outstanding loan at harvest using the seasonal surplus."
                    )
                feasible.append((msg, float(bullet.get("leftover_after_bullet", -math.inf)), bullet))

            # extend options: keep 24,36 for pool (extend_candidates[1:])
            for ext in extend_candidates[1:]:
                # try to read the new tenure, fallback to an available field
                new_tenure = int(ext.get("new_tenure_months") or ext.get("tenure") or 0)
                surplus = ext.get("surplus_after_newloan", ext.get("surplus_after_extension", None))
                surplus_val = float(surplus) if surplus is not None and not (isinstance(surplus, str) and surplus == "") else -math.inf
                surplus_fmt = _fmt_amt(surplus)
                # optional EMI info if present
                emi_after = ext.get("emi_monthly_after_extension") or ext.get("emi_after_extension") or ext.get("emi_monthly_new")
                emi_part = f" The estimated monthly payment after this change is {_fmt_amt(emi_after)}." if emi_after is not None else ""
                msg = (
                    f"Consider extending the loan tenure to {new_tenure} months to lower your monthly payments.{emi_part} "
                    f"This change is estimated to result in a seasonal surplus of about {surplus_fmt}."
                )
                feasible.append((msg, surplus_val, ext))

            # partials
            for pct, tenure, out in partials:
                # compute repay amount (prefer a provided field, else compute from principal)
                repay_amt = out.get("repay_amount")
                if repay_amt is None:
                    try:
                        repay_amt = round(float(self.i.loan_principal) * float(pct), 2)
                    except Exception:
                        repay_amt = None
                repay_fmt = _fmt_amt(repay_amt)
                surplus = out.get("surplus_after_partial_amortize", out.get("surplus_after_partial", None))
                surplus_val = float(surplus) if surplus is not None and not (isinstance(surplus, str) and surplus == "") else -math.inf
                surplus_fmt = _fmt_amt(surplus)
                msg = (
                    f"Partially repay {repay_fmt}, which is {int(pct * 100)}% of the principal, "
                    f"and amortize the remaining balance over {int(tenure)} months. "
                    f"This plan is estimated to leave a seasonal surplus of approximately {surplus_fmt}."
                )
                feasible.append((msg, surplus_val, out))

            # sort by score descending (higher seasonal surplus first)
            feasible_sorted = sorted(feasible, key=lambda x: x[1], reverse=True)

            RENAME_MAP = {
                "emi_after_amortize_monthly": "Estimated Monthly EMI After Amortize",
                "harvest_can_afford_partial": "Harvest Can Afford Partial Repayment",
                "harvest_cash": "Cash Available at Harvest",
                "is_sufficient": "Is Repayment Sufficient",
                "principal_remaining": "Principal Remaining",
                "repay_at_harvest": "Repayable at Harvest",
                "seasonal_loan_after": "Seasonal Loan Outflow After Change",
                "surplus_after_partial_amortize": "Seasonal Surplus After Plan"
            }
            DROP_KEYS = {"internal_flag", "debug_trace"} 

            for key, score, payload in feasible_sorted:
                pretty_details = prettify_details(payload, rename_map=RENAME_MAP, drop_keys=DROP_KEYS, keep_raw=False)

                recs.append({
                    "option": key,  # now a readable English sentence
                    "score_surplus": round(float(score), 2) if score is not None and not math.isinf(score) else float("-inf"),
                    "details": pretty_details
                })

        return {
            "baseline": baseline,
            "scenarios": results,
            "recommendations": recs
        }


# ---------------- Example usage with your numbers ----------------
if __name__ == "__main__":
    # Your example inputs
    fi = FarmInputs(
        area_ha=1.0,
        yield_q_per_ha=35.0,      # 35 q/ha
        price_per_q=2500.0,       # ₹2,500/q
        input_cost=25000.0,       # ₹25,000
        insurance=1000.0,         # ₹1,000
        household_monthly=13000.0,# ₹13,000/month
        off_farm_monthly=4000.0,  # ₹4,000/month
        loan_principal=40000.0,   # ₹40,000
        annual_interest_rate=7.0, # 7% p.a.
        loan_tenure_months=12,    # baseline 12 months EMI
        marketing_deduction_pct=0.02,
        harvest_months=[4]        # harvest in April (month 4)
    )

    mgr = FarmDebtManager(fi)
    out = mgr.recommend()

    # pretty print summary
    print("=== Baseline summary ===")
    print(json.dumps(out["baseline"], indent=2))
    print("\n=== Top recommended options (sorted by surplus) ===")
    # show top 6
    for rec in out["recommendations"][:6]:
        print("-", rec["option"], "| surplus:", rec["score_surplus"])
        # print compact detail
        d = rec["details"]
        # show only key fields (stringify safely)
        print("   detail keys:", list(d.keys()))
