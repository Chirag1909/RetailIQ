"""
RetailIQ - Customer RFM Segmentation & Behavior Engine (backend/app/analytics/rfm.py)
Implements transparent quintile-based Recency, Frequency, Monetary (RFM) segmentation,
cohort analysis, and customer revenue concentration scoring.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


class CustomerRFMAnalyzer:
    """Computes transparent RFM segmentation and customer intelligence metrics."""

    SEGMENT_DESCRIPTIONS = {
        "Champions": "High recency, high frequency, and high monetary spend. Best customers who advocate and spend regularly.",
        "Loyal Customers": "Consistent purchase history and good spend. Highly responsive to new promotions.",
        "Potential Loyalists": "Recent customers with above-average frequency and spend. Candidates for loyalty program onboarding.",
        "At Risk": "High spenders in the past who have not purchased recently. Require targeted win-back retention campaigns.",
        "Hibernating": "Low recency, low frequency, and low spend. Likely churned accounts requiring reactivation discounts.",
        "Promising / Standard": "Average spenders and buyers with standard commercial patterns."
    }

    @staticmethod
    def classify_rfm_segment(r_score: int, f_score: int, m_score: int) -> str:
        """
        Transparent business logic mapping quintile scores (1-5, where 5 is best) to segments.
        """
        # Champions: R >= 4, F >= 4, M >= 4
        if r_score >= 4 and f_score >= 4 and m_score >= 4:
            return "Champions"
        # Loyal Customers: R >= 3, F >= 3
        elif r_score >= 3 and f_score >= 3:
            return "Loyal Customers"
        # Potential Loyalists: R >= 4, F >= 1, M >= 2
        elif r_score >= 4 and f_score <= 3 and m_score >= 2:
            return "Potential Loyalists"
        # At Risk: R <= 2, F >= 3, M >= 3
        elif r_score <= 2 and (f_score >= 3 or m_score >= 3):
            return "At Risk"
        # Hibernating: R <= 2, F <= 2
        elif r_score <= 2 and f_score <= 2:
            return "Hibernating"
        else:
            return "Promising / Standard"

    @classmethod
    def analyze_rfm(cls, customer_metrics_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Processes customer metrics dataframe, assigns quintile scores and segments.
        """
        df = customer_metrics_df.copy()
        if len(df) == 0:
            return {"segments": {}, "summary": {}}

        # Quintile scoring (1-5)
        # Recency: lower recency_days = better (score 5 for lowest days)
        # Frequency: higher order_count = better (score 5 for highest orders)
        # Monetary: higher total_spend = better (score 5 for highest spend)
        df["r_score"] = pd.qcut(df["recency_days"], q=5, labels=[5, 4, 3, 2, 1]).astype(int)
        
        # Frequency often has many 1-purchase customers, so use rank method for ties
        df["f_score"] = pd.qcut(df["order_count"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
        df["m_score"] = pd.qcut(df["total_spend"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)

        df["segment"] = df.apply(
            lambda row: cls.classify_rfm_segment(row["r_score"], row["f_score"], row["m_score"]),
            axis=1
        )

        total_customers = len(df)
        total_revenue = float(df["total_spend"].sum())

        # Segment breakdown
        segment_summary = []
        for segment, grp in df.groupby("segment"):
            seg_cust_count = len(grp)
            seg_spend = float(grp["total_spend"].sum())
            segment_summary.append({
                "segment": segment,
                "customer_count": seg_cust_count,
                "customer_pct": round((seg_cust_count / total_customers) * 100, 2),
                "total_spend": round(seg_spend, 2),
                "spend_pct": round((seg_spend / total_revenue) * 100, 2),
                "avg_recency_days": round(float(grp["recency_days"].mean()), 1),
                "avg_frequency": round(float(grp["order_count"].mean()), 1),
                "avg_monetary": round(float(grp["total_spend"].mean()), 2),
                "description": cls.SEGMENT_DESCRIPTIONS.get(segment, "")
            })

        # Order by total spend descending
        segment_summary.sort(key=lambda x: x["total_spend"], reverse=True)

        return {
            "summary": {
                "total_identified_customers": total_customers,
                "total_historical_spend": round(total_revenue, 2),
                "avg_customer_lifetime_spend": round(total_revenue / total_customers, 2),
                "repeat_customer_count": int((df["order_count"] > 1).sum()),
                "repeat_customer_rate_pct": round(((df["order_count"] > 1).sum() / total_customers) * 100, 2)
            },
            "segment_distribution": segment_summary,
            "segmented_df": df
        }
