"""
Phase 7 — Dashboard Service

Provides real, database-derived aggregations for the DRIFT Intelligence Dashboard:
- Executive Summary & Comparison
- Trend Points (7d, 30d, 90d, 12m)
- Site & Functional Location Intelligence (with normalized density or concentration fallback)
- Activity Intelligence
- Hazard Intelligence
- Life-Saving Rule (9 LSRs) Intelligence
- Barrier Intelligence & Weakness Ranking (INTACT, DEGRADED, FAILED, ABSENT, UNKNOWN)
- Escalating Precursor Patterns & Top Recurring Mechanisms
- Recent Alerts
- Data Quality & Coverage
"""

from typing import List, Optional, Dict, Any, cast
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct, case, text

from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.models.clusters import Cluster, ClusterMember
from app.models.alerts import Alert
from app.models.embeddings import ReportEmbedding
from app.schemas.enums import (
    SifDecision,
    PriorityLevel,
    BarrierCondition,
    AnalysisStatus,
    EscalationBand,
    OFFICIAL_LIFE_SAVING_RULES,
)
from app.schemas.dashboard_schemas import (
    DashboardSummary,
    TrendPoint,
    SiteSummary,
    ActivitySummary,
    HazardSummary,
    LsrSummary,
    BarrierSummary,
    RecurringMechanismSummary,
    RecentAlertSummary,
    DataQualitySummary,
)
from app.utils.logging import logger


class DashboardService:

    @staticmethod
    def _build_report_filters(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        site: Optional[str] = None,
        unit: Optional[str] = None,
        functional_location: Optional[str] = None,
        employment_type: Optional[str] = None,
        sif_status: Optional[str] = None,
        priority_level: Optional[str] = None,
        lsr: Optional[str] = None,
        activity: Optional[str] = None,
        hazard: Optional[str] = None,
        barrier_condition: Optional[str] = None,
    ) -> List[Any]:
        """Constructs SQL filters matching both Report and joined SafetyAnalysis fields."""
        filters = []
        if start_date:
            filters.append(Report.report_date >= start_date)
        if end_date:
            filters.append(Report.report_date <= end_date)
        if site:
            filters.append(Report.site.ilike(f"%{site}%"))
        if unit:
            filters.append(Report.unit.ilike(f"%{unit}%"))
        if functional_location:
            filters.append(Report.functional_location.ilike(f"%{functional_location}%"))
        if employment_type:
            filters.append(Report.employee_or_contractor.ilike(f"%{employment_type}%"))
        if sif_status:
            filters.append(SafetyAnalysis.sif_fpi_potential == sif_status)
        if priority_level:
            filters.append(SafetyAnalysis.priority_level == priority_level)
        if lsr:
            filters.append(
                or_(
                    SafetyAnalysis.primary_life_saving_rule == lsr,
                    SafetyAnalysis.life_saving_rule == lsr,
                )
            )
        if activity:
            filters.append(SafetyAnalysis.activity.ilike(f"%{activity}%"))
        if hazard:
            filters.append(SafetyAnalysis.hazard.ilike(f"%{hazard}%"))
        if barrier_condition:
            filters.append(SafetyAnalysis.barrier_condition == barrier_condition)
        return filters

    @classmethod
    async def get_summary(
        cls,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        site: Optional[str] = None,
        unit: Optional[str] = None,
        functional_location: Optional[str] = None,
        employment_type: Optional[str] = None,
        sif_status: Optional[str] = None,
        priority_level: Optional[str] = None,
        lsr: Optional[str] = None,
        activity: Optional[str] = None,
        hazard: Optional[str] = None,
        barrier_condition: Optional[str] = None,
    ) -> DashboardSummary:
        filters = cls._build_report_filters(
            start_date, end_date, site, unit, functional_location, employment_type,
            sif_status, priority_level, lsr, activity, hazard, barrier_condition
        )

        query = (
            select(
                func.count(Report.id).label("total"),
                func.count(case((SafetyAnalysis.analysis_status == AnalysisStatus.COMPLETED, 1))).label("analyzed"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.YES, 1))).label("sif_yes"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.NO, 1))).label("sif_no"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.UNCERTAIN, 1))).label("sif_uncertain"),
                func.count(case((SafetyAnalysis.priority_level == PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR, 1))).label("high_priority"),
                func.count(case((SafetyAnalysis.priority_level == PriorityLevel.CRITICAL, 1))).label("critical"),
            )
            .outerjoin(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
        )
        if filters:
            query = query.where(and_(*filters))

        res = await db.execute(query)
        row = res.one()

        total = row.total or 0
        analyzed = row.analyzed or 0
        sif_yes = row.sif_yes or 0
        sif_no = row.sif_no or 0
        sif_uncertain = row.sif_uncertain or 0
        high_priority = row.high_priority or 0
        critical = row.critical or 0

        sif_share_pct = round((sif_yes / analyzed * 100.0), 1) if analyzed > 0 else None

        # Cluster metrics
        cluster_query = select(
            func.count(Cluster.id).label("total_clusters"),
            func.count(case((Cluster.escalation_score >= 60.0, 1))).label("escalating_clusters"),
        )
        c_res = await db.execute(cluster_query)
        c_row = c_res.one()
        active_clusters = c_row.total_clusters or 0
        escalating_clusters = c_row.escalating_clusters or 0

        return DashboardSummary(
            total_reports=total,
            analyzed_reports=analyzed,
            sif_yes=sif_yes,
            sif_no=sif_no,
            sif_uncertain=sif_uncertain,
            high_priority=high_priority,
            critical=critical,
            escalating_clusters=escalating_clusters,
            active_clusters=active_clusters,
            sif_share_pct=sif_share_pct,
            comparison_period_label="No comparison data",
            total_reports_change_pct=None,
            sif_yes_change_pct=None,
            high_priority_change_pct=None,
        )

    @classmethod
    async def get_trends(
        cls,
        db: AsyncSession,
        window: str = "30d",
        site: Optional[str] = None,
        lsr: Optional[str] = None,
        priority_level: Optional[str] = None,
    ) -> List[TrendPoint]:
        """Returns time series aggregated points by date."""
        today = date.today()
        if window == "7d":
            start_date = today - timedelta(days=7)
        elif window == "90d":
            start_date = today - timedelta(days=90)
        elif window == "12m":
            start_date = today - timedelta(days=365)
        else:  # default 30d
            start_date = today - timedelta(days=30)

        filters = cls._build_report_filters(
            start_date=start_date, site=site, lsr=lsr, priority_level=priority_level
        )

        query = (
            select(
                Report.report_date.label("date"),
                func.count(Report.id).label("total"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.YES, 1))).label("sif_yes"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.UNCERTAIN, 1))).label("sif_uncertain"),
                func.count(case((SafetyAnalysis.priority_level.in_([PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR, PriorityLevel.CRITICAL]), 1))).label("high_priority"),
            )
            .outerjoin(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
            .where(Report.report_date.isnot(None))
        )
        if filters:
            query = query.where(and_(*filters))

        query = query.group_by(Report.report_date).order_by(Report.report_date.asc())

        res = await db.execute(query)
        rows = res.all()

        return [
            TrendPoint(
                date=r.date.isoformat() if r.date else "",
                total_reports=r.total or 0,
                sif_yes=r.sif_yes or 0,
                sif_uncertain=r.sif_uncertain or 0,
                high_priority=r.high_priority or 0,
            )
            for r in rows
        ]

    @classmethod
    async def get_sites(
        cls,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[SiteSummary]:
        filters = cls._build_report_filters(start_date=start_date, end_date=end_date)

        query = (
            select(
                Report.site.label("site"),
                func.count(Report.id).label("total"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.YES, 1))).label("sif_count"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.UNCERTAIN, 1))).label("sif_uncertain_count"),
                func.count(case((SafetyAnalysis.priority_level == PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR, 1))).label("high_priority_count"),
                func.count(case((SafetyAnalysis.priority_level == PriorityLevel.CRITICAL, 1))).label("critical_count"),
                func.coalesce(func.sum(Report.man_hours), 0.0).label("man_hours"),
                func.count(case((SafetyAnalysis.barrier_condition.in_([BarrierCondition.DEGRADED, BarrierCondition.FAILED, BarrierCondition.ABSENT]), 1))).label("barrier_weakness"),
            )
            .outerjoin(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
            .where(Report.site.isnot(None))
        )
        if filters:
            query = query.where(and_(*filters))

        query = query.group_by(Report.site).order_by(text("sif_count DESC, critical_count DESC, total DESC"))

        res = await db.execute(query)
        rows = res.all()

        # Query cluster counts per site
        cluster_site_query = (
            select(
                Report.site.label("site"),
                func.count(distinct(ClusterMember.cluster_id)).label("cluster_count"),
                func.count(distinct(case((Cluster.escalation_score >= 60.0, ClusterMember.cluster_id)))).label("escalating_cluster_count"),
            )
            .join(ClusterMember, Report.report_id == ClusterMember.report_id)
            .join(Cluster, ClusterMember.cluster_id == Cluster.id)
            .where(Report.site.isnot(None))
            .group_by(Report.site)
        )
        c_res = await db.execute(cluster_site_query)
        c_map = {r.site: (r.cluster_count or 0, r.escalating_cluster_count or 0) for r in c_res.all()}

        summaries = []
        for r in rows:
            site_name = r.site
            total = r.total or 0
            sif = r.sif_count or 0
            man_hours = float(r.man_hours or 0.0)

            # Density check
            has_valid_man_hours = man_hours > 100.0  # meaningful denominator check
            density = None
            density_unit = None
            if has_valid_man_hours:
                # Precursor density per 10,000 man-hours
                density = round((sif / man_hours) * 10000.0, 2)
                density_unit = "per 10k man-hours"

            # Fallback precursor concentration %
            concentration = round((sif / total * 100.0), 1) if total > 0 else 0.0

            c_count, esc_count = c_map.get(site_name, (0, 0))

            summaries.append(
                SiteSummary(
                    site=site_name,
                    report_count=total,
                    sif_count=sif,
                    sif_uncertain_count=r.sif_uncertain_count or 0,
                    high_priority_count=r.high_priority_count or 0,
                    critical_count=r.critical_count or 0,
                    cluster_count=c_count,
                    escalating_cluster_count=esc_count,
                    total_man_hours=round(man_hours, 1),
                    precursor_density=density,
                    precursor_density_unit=density_unit,
                    precursor_concentration_pct=concentration,
                    has_valid_man_hours=has_valid_man_hours,
                    barrier_weakness_count=r.barrier_weakness or 0,
                )
            )

        return summaries

    @classmethod
    async def get_activities(
        cls,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[ActivitySummary]:
        filters = cls._build_report_filters(start_date=start_date, end_date=end_date)
        filters.append(SafetyAnalysis.activity.isnot(None))
        filters.append(SafetyAnalysis.activity != "UNKNOWN")

        query = (
            select(
                SafetyAnalysis.activity.label("activity"),
                func.count(Report.id).label("total"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.YES, 1))).label("sif_count"),
                func.count(case((SafetyAnalysis.priority_level.in_([PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR, PriorityLevel.CRITICAL]), 1))).label("high_priority_count"),
            )
            .join(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
            .where(and_(*filters))
            .group_by(SafetyAnalysis.activity)
            .order_by(text("sif_count DESC, total DESC"))
            .limit(15)
        )

        res = await db.execute(query)
        rows = res.all()

        return [
            ActivitySummary(
                activity=r.activity,
                report_count=r.total or 0,
                sif_count=r.sif_count or 0,
                high_priority_count=r.high_priority_count or 0,
                cluster_count=0,
                escalation_score=0.0,
            )
            for r in rows
        ]

    @classmethod
    async def get_hazards(
        cls,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[HazardSummary]:
        filters = cls._build_report_filters(start_date=start_date, end_date=end_date)
        filters.append(SafetyAnalysis.hazard.isnot(None))
        filters.append(SafetyAnalysis.hazard != "UNKNOWN")

        query = (
            select(
                SafetyAnalysis.hazard.label("hazard"),
                func.count(Report.id).label("total"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.YES, 1))).label("sif_count"),
                func.count(case((SafetyAnalysis.priority_level.in_([PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR, PriorityLevel.CRITICAL]), 1))).label("high_priority_count"),
            )
            .join(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
            .where(and_(*filters))
            .group_by(SafetyAnalysis.hazard)
            .order_by(text("sif_count DESC, total DESC"))
            .limit(15)
        )

        res = await db.execute(query)
        rows = res.all()

        return [
            HazardSummary(
                hazard=r.hazard,
                report_count=r.total or 0,
                sif_count=r.sif_count or 0,
                high_priority_count=r.high_priority_count or 0,
                associated_lsrs=[],
                associated_barriers=[],
                associated_clusters=[],
            )
            for r in rows
        ]

    @classmethod
    async def get_lsr(
        cls,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[LsrSummary]:
        filters = cls._build_report_filters(start_date=start_date, end_date=end_date)

        query = (
            select(
                func.coalesce(SafetyAnalysis.primary_life_saving_rule, SafetyAnalysis.life_saving_rule).label("lsr"),
                func.count(Report.id).label("total"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.YES, 1))).label("sif_count"),
                func.count(case((SafetyAnalysis.priority_level == PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR, 1))).label("high_priority_count"),
                func.count(case((SafetyAnalysis.priority_level == PriorityLevel.CRITICAL, 1))).label("critical_count"),
            )
            .join(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
        )
        if filters:
            query = query.where(and_(*filters))

        query = query.group_by("lsr")

        res = await db.execute(query)
        rows = res.all()
        db_map = {r.lsr: r for r in rows if r.lsr}

        # Query escalating clusters by common_lsr
        cl_res = await db.execute(
            select(Cluster.common_lsr, func.count(Cluster.id))
            .where(Cluster.escalation_score >= 60.0)
            .group_by(Cluster.common_lsr)
        )
        cl_map = {r[0]: r[1] for r in cl_res.all() if r[0]}

        # Represent all 9 official project Life-Saving Rules
        lsr_list = []
        for official in OFFICIAL_LIFE_SAVING_RULES:
            r = db_map.get(official)
            mapped_count = r.total if r else 0
            sif_count = r.sif_count if r else 0
            hp_count = r.high_priority_count if r else 0
            crit_count = r.critical_count if r else 0
            esc_clusters = cl_map.get(official, 0)

            lsr_list.append(
                LsrSummary(
                    lsr=official,
                    mapped_count=mapped_count,
                    sif_yes_count=sif_count,
                    high_priority_count=hp_count,
                    critical_count=crit_count,
                    escalating_cluster_count=esc_clusters,
                )
            )

        # Sort by sif_yes_count descending, then mapped_count descending
        lsr_list.sort(key=lambda x: (x.sif_yes_count, x.high_priority_count, x.mapped_count), reverse=True)
        return lsr_list

    @classmethod
    async def get_barriers(
        cls,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[BarrierSummary]:
        filters = cls._build_report_filters(start_date=start_date, end_date=end_date)
        filters.append(SafetyAnalysis.barrier.isnot(None))
        filters.append(SafetyAnalysis.barrier != "UNKNOWN")

        query = (
            select(
                SafetyAnalysis.barrier.label("barrier"),
                func.count(Report.id).label("total"),
                func.count(case((SafetyAnalysis.barrier_condition == BarrierCondition.INTACT, 1))).label("intact"),
                func.count(case((SafetyAnalysis.barrier_condition == BarrierCondition.DEGRADED, 1))).label("degraded"),
                func.count(case((SafetyAnalysis.barrier_condition == BarrierCondition.FAILED, 1))).label("failed"),
                func.count(case((SafetyAnalysis.barrier_condition == BarrierCondition.ABSENT, 1))).label("absent"),
                func.count(case((SafetyAnalysis.barrier_condition == BarrierCondition.UNKNOWN, 1))).label("unknown"),
                func.count(case((SafetyAnalysis.sif_fpi_potential == SifDecision.YES, 1))).label("sif_count"),
                func.count(case((SafetyAnalysis.priority_level.in_([PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR, PriorityLevel.CRITICAL]), 1))).label("high_priority_count"),
            )
            .join(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
            .where(and_(*filters))
            .group_by(SafetyAnalysis.barrier)
        )

        res = await db.execute(query)
        rows = res.all()

        barriers = []
        for r in rows:
            failed = r.failed or 0
            absent = r.absent or 0
            degraded = r.degraded or 0
            # Weakness ranking formula: failed * 3.0 + absent * 3.0 + degraded * 1.5
            weakness_score = round(failed * 3.0 + absent * 3.0 + degraded * 1.5, 1)

            barriers.append(
                BarrierSummary(
                    barrier=r.barrier,
                    total_mentions=r.total or 0,
                    intact_count=r.intact or 0,
                    degraded_count=degraded,
                    failed_count=failed,
                    absent_count=absent,
                    unknown_count=r.unknown or 0,
                    sif_count=r.sif_count or 0,
                    high_priority_count=r.high_priority_count or 0,
                    escalating_cluster_count=0,
                    weakness_score=weakness_score,
                )
            )

        # Sort by weakness_score descending
        barriers.sort(key=lambda b: (b.weakness_score, b.failed_count + b.absent_count, b.degraded_count), reverse=True)
        return barriers

    @classmethod
    async def get_recurring_mechanisms(
        cls,
        db: AsyncSession,
    ) -> List[RecurringMechanismSummary]:
        """Returns top recurring precursor patterns from cluster intelligence."""
        query = (
            select(Cluster)
            .order_by(Cluster.escalation_score.desc(), Cluster.recurrence_count.desc())
            .limit(10)
        )
        res = await db.execute(query)
        raw_clusters = res.scalars().all()

        return [
            RecurringMechanismSummary(
                mechanism_name=str(c.cluster_name or ""),
                report_count=int(c.recurrence_count or 0),
                sif_count=int(c.recurrence_count or 0),  # pre-screened in cluster
                cluster_count=1,
                escalation_score=float(c.escalation_score or 0.0),
                shared_asset=c.common_asset,
                shared_barrier=c.common_barrier,
                lsr=c.common_lsr,
            )
            for c in cast(List[Any], raw_clusters)
        ]

    @classmethod
    async def get_alerts(
        cls,
        db: AsyncSession,
        limit: int = 10,
    ) -> List[RecentAlertSummary]:
        query = (
            select(Alert, Cluster)
            .outerjoin(Cluster, Alert.cluster_id == Cluster.id)
            .order_by(Alert.created_at.desc(), Alert.score.desc())
            .limit(limit)
        )
        res = await db.execute(query)
        rows = res.all()

        alerts = []
        for alert, cluster in rows:
            loc = cluster.common_asset if cluster else None
            mech = cluster.common_mechanism if cluster else None
            alerts.append(
                RecentAlertSummary(
                    id=alert.id,
                    created_at=alert.created_at.strftime("%Y-%m-%d %H:%M") if alert.created_at else "",
                    cluster_id=alert.cluster_id,
                    cluster_name=cluster.cluster_name if cluster else "Precursor Pattern",
                    escalation_score=alert.score or 0.0,
                    priority=alert.priority or "HIGH",
                    mechanism=mech,
                    location=loc,
                    reason=alert.message or "Precursor recurrence accumulation detected.",
                )
            )
        return alerts

    @classmethod
    async def get_data_quality(cls, db: AsyncSession) -> DataQualitySummary:
        total_res = await db.execute(select(func.count(Report.id)))
        total_reports = total_res.scalar_one() or 0

        # Analysis status counts
        status_query = select(
            func.count(case((SafetyAnalysis.analysis_status == AnalysisStatus.COMPLETED, 1))).label("completed"),
            func.count(case((SafetyAnalysis.analysis_status == AnalysisStatus.FAILED, 1))).label("failed"),
            func.count(case((SafetyAnalysis.sif_fpi_potential.isnot(None), 1))).label("sif_screened"),
            func.count(case((SafetyAnalysis.primary_life_saving_rule.isnot(None), 1))).label("lsr_mapped"),
        )
        s_res = await db.execute(status_query)
        s_row = s_res.one()

        completed = s_row.completed or 0
        failed = s_row.failed or 0
        not_analyzed = max(0, total_reports - completed - failed)
        sif_screened = s_row.sif_screened or 0
        lsr_mapped = s_row.lsr_mapped or 0

        # Embeddings & cluster coverage
        emb_res = await db.execute(select(func.count(ReportEmbedding.id)))
        emb_count = emb_res.scalar_one() or 0
        emb_pct = round((emb_count / total_reports * 100.0), 1) if total_reports > 0 else 0.0

        cl_res = await db.execute(select(func.count(distinct(ClusterMember.report_id))))
        clustered_reports = cl_res.scalar_one() or 0

        # Field completeness
        fields_to_check = [
            ("narrative", Report.narrative),
            ("functional_location", Report.functional_location),
            ("man_hours", Report.man_hours),
            ("site", Report.site),
            ("incident_cause", Report.incident_cause),
        ]
        completeness = {}
        for name, col in fields_to_check:
            c_res = await db.execute(select(func.count(Report.id)).where(col.isnot(None)))
            present = c_res.scalar_one() or 0
            completeness[name] = round((present / total_reports * 100.0), 1) if total_reports > 0 else 0.0

        return DataQualitySummary(
            total_imported=total_reports,
            analyzed_count=completed,
            not_analyzed_count=not_analyzed,
            failed_analysis_count=failed,
            sif_screened_count=sif_screened,
            lsr_mapped_count=lsr_mapped,
            embedding_coverage_pct=emb_pct,
            clustered_reports_count=clustered_reports,
            field_completeness=completeness,
        )
