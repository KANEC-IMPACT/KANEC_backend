from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class CategoryDistribution(BaseModel):
    category: str
    percentage: float
    amount: float

class MostSupportedCategory(BaseModel):
    category: str
    percentage: float
    growth_percentage: float
    total_donated: float

class FrequencyTrend(BaseModel):
    trend: str  # "increasing", "decreasing", "stable"
    change_percentage: float
    average_monthly_donations: float

class ImpactFactors(BaseModel):
    total_amount: float
    consistency: float
    diversity: float
    recent_activity: float
    generosity: float

class ImpactScore(BaseModel):
    score: int
    level: str  # "Beginner", "Starter", "Contributor", "Supporter", "Champion"
    factors: ImpactFactors

class MonthlyTrend(BaseModel):
    month: str
    total_donated: float
    donation_count: int
    average_donation: float

class RecommendedProject(BaseModel):
    id: str
    title: str
    category: str
    description: str
    amount_raised: float
    target_amount: float
    completion_percentage: float
    reason: str

class UserPercentile(BaseModel):
    percentile: float
    rank: int
    total_donors: int
    description: str

class DonationSummary(BaseModel):
    total_donated: float
    total_donations: int
    average_donation: float
    largest_donation: float
    first_donation: Optional[str]
    last_donation: Optional[str]

class UserInsights(BaseModel):
    category_distribution: Dict[str, float]
    most_supported_category: MostSupportedCategory
    donation_frequency_trend: FrequencyTrend
    user_impact_score: ImpactScore
    monthly_trends: List[MonthlyTrend]
    recommended_projects: List[RecommendedProject]
    user_percentile: UserPercentile
    donation_summary: DonationSummary
    message: Optional[str] = None

class UserInsightsResponse(BaseModel):
    user_id: str
    user_email: str
    insights: UserInsights

class GlobalStats(BaseModel):
    total_donations: int
    total_amount_raised: float
    total_projects: int
    total_donors: int
    average_donation: float

class CategoryAnalytics(BaseModel):
    category: str
    total_raised: float
    project_count: int
    donation_count: int
    average_donation: float
    percentage_of_total: float

class PlatformAnalytics(BaseModel):
    global_stats: GlobalStats
    top_categories: List[CategoryAnalytics]
    recent_activity: Dict[str, Any]

class ProjectAnalytics(BaseModel):
    project_id: str
    project_title: str
    total_raised: float
    donation_count: int
    average_donation: float
    completion_percentage: float
    donor_count: int
    recent_donations: List[Dict[str, Any]]