import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from collections import Counter
import logging
from uuid import UUID
from api.v1.models.donation import Donation, DonationStatus
from api.v1.models.project import Project



logger = logging.getLogger(__name__)

class DonationAnalytics:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_insights(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive AI-powered insights for a user.
        """
        try:
            
            donations = self.db.query(Donation).options(
                joinedload(Donation.project)
            ).filter(
                Donation.donor_id == user_id,
                Donation.status == DonationStatus.completed
            ).all()
            
            if not donations:
                return self._get_empty_insights()
            
            df = self._donations_to_dataframe(donations)
            
            insights = {
                "category_distribution": self._get_category_distribution(df),
                "most_supported_category": self._get_most_supported_category(df),
                "donation_frequency_trend": self._get_frequency_trend(df),
                "user_impact_score": self._calculate_impact_score(df),
                "monthly_trends": self._get_monthly_trends(df),
                "recommended_projects": await self._get_recommended_projects(user_id, df, self.db),
                "user_percentile": self._calculate_user_percentile(user_id, df, self.db),
                "donation_summary": self._get_donation_summary(df)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return self._get_empty_insights()
    
    def _donations_to_dataframe(self, donations: List) -> pd.DataFrame:
        """Convert donations to pandas DataFrame for analysis."""
        data = []
        for donation in donations:
            project_category = getattr(donation.project, 'category', 'Unknown') if donation.project else 'Unknown'
            project_title = getattr(donation.project, 'title', 'Unknown') if donation.project else 'Unknown'
            
            data.append({
                'id': str(donation.id),
                'amount': donation.amount,
                'created_at': donation.created_at,
                'project_id': str(donation.project_id),
                'project_title': project_title,
                'category': project_category,
                'status': donation.status.value
            })
        return pd.DataFrame(data)
    
    def _get_category_distribution(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate percentage distribution of supported categories."""
        if df.empty:
            return {}
        
        category_totals = df.groupby('category')['amount'].sum()
        total_donated = category_totals.sum()
        
        distribution = {}
        for category, amount in category_totals.items():
            percentage = (amount / total_donated) * 100
            distribution[category] = round(percentage, 2)
        
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
    
    def _get_most_supported_category(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get the most supported category and its growth."""
        if df.empty:
            return {
                "category": "None", 
                "percentage": 0.0, 
                "growth_percentage": 0.0,
                "total_donated": 0.0
            }
        
        try:
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            current_month_ts = pd.Timestamp(current_month)
            
            if not df.empty and hasattr(df['created_at'].iloc[0], 'tz') and df['created_at'].iloc[0].tz is not None:
                current_month_ts = current_month_ts.tz_localize('UTC').tz_convert(df['created_at'].iloc[0].tz)
            
            current_data = df[df['created_at'] >= current_month_ts]
            
            if current_data.empty:
                category_totals = df.groupby('category')['amount'].sum()
                if category_totals.empty:
                    return {
                        "category": "None",
                        "percentage": 0.0,
                        "growth_percentage": 0.0,
                        "total_donated": 0.0
                    }
                
                most_supported = category_totals.idxmax()
                total_all_time = df['amount'].sum()
                percentage = (category_totals.max() / total_all_time * 100) if total_all_time > 0 else 0
                
                return {
                    "category": str(most_supported),
                    "percentage": round(float(percentage), 2),
                    "growth_percentage": 0.0,
                    "total_donated": round(float(category_totals.max()), 2)
                }
            
            current_category_totals = current_data.groupby('category')['amount'].sum()
            if current_category_totals.empty:
                return {
                    "category": "None",
                    "percentage": 0.0,
                    "growth_percentage": 0.0,
                    "total_donated": 0.0
                }
            
            most_supported = current_category_totals.idxmax()
            current_total = current_data['amount'].sum()
            percentage = (current_category_totals.max() / current_total * 100) if current_total > 0 else 0
            
            previous_month = (current_month - timedelta(days=1)).replace(day=1)
            previous_month_ts = pd.Timestamp(previous_month)
            
            if not df.empty and hasattr(df['created_at'].iloc[0], 'tz') and df['created_at'].iloc[0].tz is not None:
                previous_month_ts = previous_month_ts.tz_localize('UTC').tz_convert(df['created_at'].iloc[0].tz)
            
            prev_data = df[
                (df['created_at'] >= previous_month_ts) & 
                (df['created_at'] < current_month_ts)
            ]
            
            growth = self._calculate_category_growth(str(most_supported), current_data, prev_data)
            
            return {
                "category": str(most_supported),
                "percentage": round(float(percentage), 2),
                "growth_percentage": round(float(growth), 2),
                "total_donated": round(float(current_category_totals.max()), 2)
            }
            
        except Exception as e:
            logger.error(f"Error in _get_most_supported_category: {str(e)}")
            return {
                "category": "None", 
                "percentage": 0.0, 
                "growth_percentage": 0.0,
                "total_donated": 0.0
            }

    def _calculate_category_growth(self, category: str, current_data: pd.DataFrame, prev_data: pd.DataFrame) -> float:
        """Calculate growth percentage for a category."""
        try:
            current_amount = current_data[current_data['category'] == category]['amount'].sum()
            prev_amount = prev_data[prev_data['category'] == category]['amount'].sum()
            
            if prev_amount == 0:
                return 100.0 if current_amount > 0 else 0.0
            
            return ((current_amount - prev_amount) / prev_amount) * 100
        except Exception as e:
            logger.error(f"Error in _calculate_category_growth: {str(e)}")
            return 0.0
    
    def _get_frequency_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze donation frequency trends."""
        if df.empty:
            return {"trend": "stable", "change_percentage": 0, "average_monthly_donations": 0}
        
        df_sorted = df.sort_values('created_at')
        df_sorted['month'] = df_sorted['created_at'].dt.to_period('M')
        
        monthly_counts = df_sorted.groupby('month').size()
        
        if len(monthly_counts) < 2:
            return {
                "trend": "stable", 
                "change_percentage": 0, 
                "average_monthly_donations": round(monthly_counts.iloc[0] if len(monthly_counts) == 1 else 0, 2)
            }
        
        x = np.arange(len(monthly_counts))
        y = monthly_counts.values
        
        slope = np.polyfit(x, y, 1)[0]
        avg_frequency = np.mean(y)
        
        if avg_frequency == 0:
            change_percentage = 0
        else:
            change_percentage = (slope / avg_frequency) * 100
        
        trend = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
        
        return {
            "trend": trend,
            "change_percentage": round(change_percentage, 2),
            "average_monthly_donations": round(avg_frequency, 2)
        }
    
    def _calculate_impact_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate user impact score based on various factors."""
        if df.empty:
            return {
                "score": 0, 
                "level": "Beginner", 
                "factors": {
                    "total_amount": 0.0,
                    "consistency": 0.0, 
                    "diversity": 0.0,
                    "recent_activity": 0.0,
                    "generosity": 0.0
                }
            }
        
        factors = {}
        
        total_amount = df['amount'].sum()
        factors['total_amount'] = min(total_amount / 10, 100)  # Normalize: $10 = 1 point
        
        df['month'] = df['created_at'].dt.to_period('M')
        unique_months = df['month'].nunique()
        factors['consistency'] = min(unique_months * 15, 100)  # 15 points per month
        
        unique_categories = df['category'].nunique()
        factors['diversity'] = min(unique_categories * 25, 100)  # 25 points per category
        
        three_months_ago = datetime.now() - timedelta(days=90)
        if hasattr(df['created_at'].iloc[0], 'tz'):
            three_months_ago = pd.Timestamp(three_months_ago).tz_localize(df['created_at'].iloc[0].tz)
        
        recent_donations = df[df['created_at'] >= three_months_ago]
        factors['recent_activity'] = min(len(recent_donations) * 20, 100)
        
        avg_donation = df['amount'].mean()
        factors['generosity'] = min(avg_donation * 2, 100)  # $50 average = 100 points
        
        weights = {
            'total_amount': 0.3, 
            'consistency': 0.25, 
            'diversity': 0.2, 
            'recent_activity': 0.15,
            'generosity': 0.1
        }
        total_score = sum(factors[factor] * weight for factor, weight in weights.items())
        
        if total_score >= 80:
            level = "Champion"
        elif total_score >= 60:
            level = "Supporter" 
        elif total_score >= 40:
            level = "Contributor"
        elif total_score >= 20:
            level = "Starter"
        else:
            level = "Beginner"
        
        return {
            "score": round(total_score),
            "level": level,
            "factors": {k: round(v, 2) for k, v in factors.items()}
        }
    
    def _get_monthly_trends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get monthly donation trends."""
        if df.empty:
            return []
        
        df['month'] = df['created_at'].dt.to_period('M')
        monthly_stats = df.groupby('month').agg({
            'amount': ['sum', 'count'],
            'id': 'count'
        }).round(2)
        
        trends = []
        for month, stats in monthly_stats.iterrows():
            donation_count = stats[('id', 'count')]
            total_donated = stats[('amount', 'sum')]
            
            trends.append({
                "month": str(month),
                "total_donated": float(total_donated),
                "donation_count": int(donation_count),
                "average_donation": float(total_donated / donation_count) if donation_count > 0 else 0
            })
        
        return trends[-6:]  # Last 6 months
    
    async def _get_recommended_projects(self, user_id: UUID, df: pd.DataFrame, db: Session) -> List[Dict[str, Any]]:
        """Get project recommendations based on user's donation history."""
        
        if not df.empty:
            user_categories = df.groupby('category')['amount'].sum().nlargest(3).index.tolist()
            
            donated_project_ids = df['project_id'].tolist()
            
            recommended = db.query(Project).filter(
                Project.verified == True,
                Project.category.in_(user_categories),
                ~Project.id.in_(donated_project_ids)
            ).order_by(Project.amount_raised.desc()).limit(5).all()
            
            if recommended:
                return [{
                    "id": str(project.id),
                    "title": project.title,
                    "category": project.category,
                    "description": project.description[:100] + "..." if len(project.description) > 100 else project.description,
                    "amount_raised": project.amount_raised,
                    "target_amount": project.target_amount,
                    "completion_percentage": round((project.amount_raised / project.target_amount) * 100, 2),
                    "reason": f"Matches your interest in {project.category}"
                } for project in recommended]
        
        popular_projects = db.query(Project).filter(
            Project.verified == True
        ).order_by(Project.amount_raised.desc()).limit(5).all()
        
        return [{
            "id": str(project.id),
            "title": project.title,
            "category": project.category,
            "description": project.description[:100] + "..." if len(project.description) > 100 else project.description,
            "amount_raised": project.amount_raised,
            "target_amount": project.target_amount,
            "completion_percentage": round((project.amount_raised / project.target_amount) * 100, 2),
            "reason": "Popular project in our platform"
        } for project in popular_projects]
    
    def _calculate_user_percentile(self, user_id: UUID, df: pd.DataFrame, db: Session) -> Dict[str, Any]:
        """Calculate user percentile compared to other donors."""
        
        all_donations = db.query(Donation).filter(Donation.status == DonationStatus.completed).all()
        
        if not all_donations:
            return {"percentile": 100, "rank": 1, "total_donors": 1, "description": "Top donor"}
        
        user_totals = {}
        for donation in all_donations:
            user_id_str = str(donation.donor_id)
            user_totals[user_id_str] = user_totals.get(user_id_str, 0) + donation.amount
        
        user_total = df['amount'].sum()
        user_id_str = str(user_id)
        
        sorted_totals = sorted(user_totals.values(), reverse=True)  # Descending for ranking
        
        try:
            user_rank = sorted_totals.index(user_total) + 1
        except ValueError:
            user_rank = len(sorted_totals)
        
        percentile = (user_rank / len(sorted_totals)) * 100
        
        if percentile <= 10:
            description = "Top 10% of donors"
        elif percentile <= 25:
            description = "Top 25% of donors" 
        elif percentile <= 50:
            description = "Top 50% of donors"
        else:
            description = "Generous supporter"
        
        return {
            "percentile": round(100 - percentile, 2),  # Higher is better (inverse percentile)
            "rank": user_rank,
            "total_donors": len(user_totals),
            "description": description
        }
    
    def _get_donation_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get overall donation summary."""
        if df.empty:
            return {
                "total_donated": 0,
                "total_donations": 0,
                "average_donation": 0,
                "first_donation": None,
                "last_donation": None
            }
        
        return {
            "total_donated": round(df['amount'].sum(), 2),
            "total_donations": len(df),
            "average_donation": round(df['amount'].mean(), 2),
            "largest_donation": round(df['amount'].max(), 2),
            "first_donation": df['created_at'].min().isoformat() if not df.empty else None,
            "last_donation": df['created_at'].max().isoformat() if not df.empty else None
        }
    
    def _get_empty_insights(self) -> Dict[str, Any]:
        """Return empty insights for users with no donation history."""
        return {
            "category_distribution": {},
            "most_supported_category": {
                "category": "None", 
                "percentage": 0.0, 
                "growth_percentage": 0.0,
                "total_donated": 0.0
            },
            "donation_frequency_trend": {
                "trend": "stable", 
                "change_percentage": 0.0, 
                "average_monthly_donations": 0.0
            },
            "user_impact_score": {
                "score": 0, 
                "level": "Beginner", 
                "factors": {
                    "total_amount": 0.0,
                    "consistency": 0.0,
                    "diversity": 0.0,
                    "recent_activity": 0.0,
                    "generosity": 0.0
                }
            },
            "monthly_trends": [],
            "recommended_projects": [],
            "user_percentile": {
                "percentile": 0.0, 
                "rank": 0, 
                "total_donors": 0, 
                "description": "New donor"
            },
            "donation_summary": {
                "total_donated": 0.0,
                "total_donations": 0, 
                "average_donation": 0.0,
                "largest_donation": 0.0,
                "first_donation": None,
                "last_donation": None
            },
            "message": "Start donating to unlock personalized insights and recommendations!"
        }