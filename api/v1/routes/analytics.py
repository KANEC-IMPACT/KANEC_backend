from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from api.db.database import get_db
from api.v1.services.auth import get_current_user
from api.v1.services.analytics import DonationAnalytics
from api.v1.models.user import User
from api.v1.models.donation import Donation, DonationStatus
from api.v1.models.project import Project
from api.v1.schemas.analytics import (
    UserInsightsResponse,
    GlobalStats,
    PlatformAnalytics,
    ProjectAnalytics,
    CategoryAnalytics
)

analytics = APIRouter(prefix="/analytics", tags=["analytics"])

@analytics.get("/user/insights", response_model=UserInsightsResponse)
async def get_user_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered donation insights and personalized recommendations for the current user.
    
    Returns comprehensive analytics including:
    - Category distribution of donations
    - Most supported category with growth metrics
    - Donation frequency trends
    - User impact score and level
    - Monthly donation trends
    - Personalized project recommendations
    - User percentile ranking among all donors
    - Complete donation summary
    """
    try:
        analytics = DonationAnalytics(db)
        insights_data = await analytics.get_user_insights(current_user.id)
        
        return UserInsightsResponse(
            user_id=str(current_user.id),
            user_email=current_user.email,
            insights=insights_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@analytics.get("/global/stats", response_model=GlobalStats)
async def get_global_analytics(db: Session = Depends(get_db)):
    """
    Get global donation statistics across the entire platform.
    
    Returns:
    - Total number of donations
    - Total amount raised
    - Total number of projects
    - Total number of donors
    - Average donation amount
    """
    try:
        total_donations = db.query(Donation).filter(Donation.status == DonationStatus.completed).count()
        total_amount = db.query(func.sum(Donation.amount)).filter(Donation.status == DonationStatus.completed).scalar() or 0
        
        total_projects = db.query(Project).filter(Project.verified == True).count()
        
        total_donors = db.query(func.count(distinct(Donation.donor_id))).filter(
            Donation.status == DonationStatus.completed
        ).scalar() or 0
        
        average_donation = round(total_amount / total_donations, 2) if total_donations > 0 else 0
        
        return GlobalStats(
            total_donations=total_donations,
            total_amount_raised=round(total_amount, 2),
            total_projects=total_projects,
            total_donors=total_donors,
            average_donation=average_donation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating global stats: {str(e)}")

@analytics.get("/platform/overview", response_model=PlatformAnalytics)
async def get_platform_analytics(db: Session = Depends(get_db)):
    """
    Get comprehensive platform analytics including category breakdowns.
    
    Returns:
    - Global statistics
    - Top categories by funding
    - Recent platform activity
    """
    try:        
        total_donations = db.query(Donation).filter(Donation.status == DonationStatus.completed).count()
        total_amount = db.query(func.sum(Donation.amount)).filter(Donation.status == DonationStatus.completed).scalar() or 0
        total_projects = db.query(Project).filter(Project.verified == True).count()
        
        total_donors = db.query(func.count(distinct(Donation.donor_id))).filter(
            Donation.status == DonationStatus.completed
        ).scalar() or 0
        
        category_stats = db.query(
            Project.category,
            func.sum(Donation.amount).label('total_raised'),
            func.count(Donation.id).label('donation_count'),
            func.count(distinct(Project.id)).label('project_count')
        ).join(Donation, Donation.project_id == Project.id).filter(
            Donation.status == DonationStatus.completed
        ).group_by(Project.category).all()
        
        top_categories = []
        for category, total_raised, donation_count, project_count in category_stats:
            percentage = (total_raised / total_amount * 100) if total_amount > 0 else 0
            avg_donation = total_raised / donation_count if donation_count > 0 else 0
            
            top_categories.append(CategoryAnalytics(
                category=category,
                total_raised=round(total_raised, 2),
                project_count=project_count,
                donation_count=donation_count,
                average_donation=round(avg_donation, 2),
                percentage_of_total=round(percentage, 2)
            ))
        
        top_categories.sort(key=lambda x: x.total_raised, reverse=True)
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_donations = db.query(Donation).filter(
            Donation.status == DonationStatus.completed,
            Donation.created_at >= seven_days_ago
        ).count()
        
        recent_projects = db.query(Project).filter(
            Project.created_at >= seven_days_ago
        ).count()
        
        return PlatformAnalytics(
            global_stats=GlobalStats(
                total_donations=total_donations,
                total_amount_raised=round(total_amount, 2),
                total_projects=total_projects,
                total_donors=total_donors,
                average_donation=round(total_amount / total_donations, 2) if total_donations > 0 else 0
            ),
            top_categories=top_categories[:10],  # Top 10 categories
            recent_activity={
                "recent_donations": recent_donations,
                "recent_projects": recent_projects,
                "time_period": "last_7_days"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating platform analytics: {str(e)}")

@analytics.get("/project/{project_id}", response_model=ProjectAnalytics)
async def get_project_analytics(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get detailed analytics for a specific project.
    
    Returns:
    - Project funding statistics
    - Donation metrics
    - Recent donation activity
    """
    try:        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        donations = db.query(Donation).filter(
            Donation.project_id == project_id,
            Donation.status == DonationStatus.completed
        ).all()
        
        total_raised = sum(donation.amount for donation in donations)
        donation_count = len(donations)
        donor_count = len(set(donation.donor_id for donation in donations))
        average_donation = total_raised / donation_count if donation_count > 0 else 0
        completion_percentage = (total_raised / project.target_amount * 100) if project.target_amount > 0 else 0
        
        recent_donations = []
        for donation in donations[-10:]:  # Last 10 donations
            recent_donations.append({
                "amount": donation.amount,
                "date": donation.created_at.isoformat(),
                "donor_id": str(donation.donor_id)
            })
        
        return ProjectAnalytics(
            project_id=str(project_id),
            project_title=project.title,
            total_raised=round(total_raised, 2),
            donation_count=donation_count,
            average_donation=round(average_donation, 2),
            completion_percentage=round(completion_percentage, 2),
            donor_count=donor_count,
            recent_donations=recent_donations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating project analytics: {str(e)}")

@analytics.get("/categories/top")
async def get_top_categories(
    limit: int = Query(10, ge=1, le=50, description="Number of top categories to return"),
    db: Session = Depends(get_db)
):
    """
    Get top categories by total funding.
    
    Returns categories sorted by total amount raised.
    """
    try:        
        category_stats = db.query(
            Project.category,
            func.sum(Donation.amount).label('total_raised'),
            func.count(Donation.id).label('donation_count'),
            func.count(distinct(Project.id)).label('project_count')
        ).join(Donation, Donation.project_id == Project.id).filter(
            Donation.status == DonationStatus.completed
        ).group_by(Project.category).order_by(func.sum(Donation.amount).desc()).limit(limit).all()
        
        total_platform = db.query(func.sum(Donation.amount)).filter(
            Donation.status == DonationStatus.completed
        ).scalar() or 0
        
        categories = []
        for category, total_raised, donation_count, project_count in category_stats:
            percentage = (total_raised / total_platform * 100) if total_platform > 0 else 0
            avg_donation = total_raised / donation_count if donation_count > 0 else 0
            
            categories.append({
                "category": category,
                "total_raised": round(total_raised, 2),
                "donation_count": donation_count,
                "project_count": project_count,
                "average_donation": round(avg_donation, 2),
                "percentage_of_total": round(percentage, 2),
                "rank": len(categories) + 1
            })
        
        return {
            "categories": categories,
            "total_categories": len(categories),
            "total_platform_funding": round(total_platform, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating category analytics: {str(e)}")

@analytics.get("/user/compare")
async def compare_user_with_average(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare current user's donation behavior with platform averages.
    """
    try:        
        analytics = DonationAnalytics(db)
        user_insights = await analytics.get_user_insights(current_user.id)
        
        total_donations = db.query(Donation).filter(Donation.status == DonationStatus.completed).count()
        total_amount = db.query(func.sum(Donation.amount)).filter(Donation.status == DonationStatus.completed).scalar() or 0
        total_donors = db.query(func.count(distinct(Donation.donor_id))).filter(
            Donation.status == DonationStatus.completed
        ).scalar() or 0
        
        platform_avg_donation = total_amount / total_donations if total_donations > 0 else 0
        platform_avg_total = total_amount / total_donors if total_donors > 0 else 0
        
        user_summary = user_insights.get('donation_summary', {})
        user_avg_donation = user_summary.get('average_donation', 0)
        user_total = user_summary.get('total_donated', 0)
        
        return {
            "user_stats": {
                "total_donated": user_total,
                "average_donation": user_avg_donation,
                "total_donations": user_summary.get('total_donations', 0)
            },
            "platform_averages": {
                "average_donation": round(platform_avg_donation, 2),
                "average_total_per_donor": round(platform_avg_total, 2)
            },
            "comparison": {
                "donation_size_vs_average": round((user_avg_donation / platform_avg_donation - 1) * 100, 2) if platform_avg_donation > 0 else 0,
                "total_vs_average": round((user_total / platform_avg_total - 1) * 100, 2) if platform_avg_total > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating comparison: {str(e)}")