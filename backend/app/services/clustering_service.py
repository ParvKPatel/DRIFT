"""
Phase 6 — Precursor Clustering Service

Groups related safety reports into precursor clusters based on semantic similarity
and common safety mechanisms (activity, hazard, equipment, barrier, LSR, location).

Maintains DB persistence for Cluster, ClusterMember, and Pattern Escalation Alerts.
"""

import json
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.config import settings
from app.schemas.enums import EscalationBand, PriorityLevel, AlertType
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.models.embeddings import ReportEmbedding
from app.models.clusters import Cluster, ClusterMember
from app.models.alerts import Alert
from app.schemas.cluster_schemas import (
    ClusterResponse,
    ClusterDetailResponse,
    ClusterMemberResponse,
    TimelineEvent,
    ClusterRebuildResponse,
)
from app.services.embedding_provider import EmbeddingFactory
from app.services.semantic_representation import SemanticRepresentationService
from app.services.similarity_engine import SimilarityEngine
from app.services.escalation_engine import EscalationEngine
from app.utils.logging import logger


class ClusteringService:
    """Orchestrates precursor clustering, cluster naming, and pattern alerts."""

    @classmethod
    async def rebuild_clusters(cls, db: AsyncSession) -> ClusterRebuildResponse:
        """
        Recomputes similarity graph and rebuilds precursor clusters across all analyzed reports.
        """
        logger.info("[ClusteringService] Starting precursor cluster rebuild...")
        now = datetime.now(timezone.utc)

        # Load all reports with safety_analysis and embeddings
        stmt = select(Report).options(selectinload(Report.safety_analysis))
        res = await db.execute(stmt)
        reports = res.scalars().all()

        if not reports:
            return ClusterRebuildResponse(
                total_reports_processed=0,
                total_clusters_formed=0,
                high_escalation_clusters=0,
                rebuilt_at=now,
            )

        # Pre-load embeddings for all reports
        embeddings_map: Dict[str, List[float]] = {}
        for r in reports:
            rid = str(r.report_id)
            emb_stmt = select(ReportEmbedding).where(ReportEmbedding.report_id == rid)
            emb_res = await db.execute(emb_stmt)
            emb = emb_res.scalar_one_or_none()
            if emb and emb.embedding is not None:
                emb_val: Any = emb.embedding
                vec = emb_val if isinstance(emb_val, list) else list(emb_val)
                embeddings_map[rid] = vec
            else:
                canonical = SemanticRepresentationService.build_canonical_text(r, r.safety_analysis)
                vec = EmbeddingFactory.get_provider().embed_text(canonical)
                db.add(ReportEmbedding(
                    report_id=rid,
                    embedding=vec,
                    canonical_text=canonical,
                    model_name=settings.EMBEDDING_MODEL,
                ))
                embeddings_map[rid] = vec

        await db.commit()

        # Build similarity graph edges (undirected)
        report_ids: List[str] = [str(r.report_id) for r in reports]
        report_by_id: Dict[str, Any] = {str(r.report_id): r for r in reports}
        n = len(reports)
        edge_threshold = settings.CLUSTER_EDGE_THRESHOLD

        adj: Dict[str, List[Tuple[str, float]]] = {rid: [] for rid in report_ids}

        for i in range(n):
            r1 = reports[i]
            r1_id = str(r1.report_id)
            v1 = embeddings_map[r1_id]
            for j in range(i + 1, n):
                r2 = reports[j]
                r2_id = str(r2.report_id)
                v2 = embeddings_map[r2_id]

                sim, _ = SimilarityEngine.calculate_hybrid_similarity(
                    r1=r1, sa1=r1.safety_analysis, v1=v1,
                    r2=r2, sa2=r2.safety_analysis, v2=v2,
                )

                if sim >= edge_threshold:
                    adj[r1_id].append((r2_id, sim))
                    adj[r2_id].append((r1_id, sim))

        # Find connected components using BFS
        visited: Set[str] = set()
        components: List[List[Tuple[str, float]]] = []

        for rid in report_ids:
            if rid not in visited:
                comp: List[Tuple[str, float]] = []
                queue: List[str] = [rid]
                visited.add(rid)

                while queue:
                    curr = queue.pop(0)
                    # Average similarity to component members
                    sims = [s for neighbor, s in adj[curr] if neighbor in [c[0] for c in comp]]
                    avg_s = sum(sims) / float(len(sims)) if sims else 1.0
                    comp.append((curr, avg_s))

                    for neighbor, s in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

                components.append(comp)

        # Clear existing clusters & cluster_members
        await db.execute(delete(ClusterMember))
        await db.execute(delete(Cluster))
        await db.commit()

        high_escalation_count = 0

        # Create Cluster records
        for comp in components:
            member_tuples = []
            for rid, sim in comp:
                r = report_by_id[rid]
                sa = r.safety_analysis
                member_tuples.append((r, sa, sim))

            # Calculate common attributes
            common_act = cls._most_frequent([m[1].activity for m in member_tuples if m[1] and m[1].activity and m[1].activity != "UNKNOWN"])
            common_haz = cls._most_frequent([m[1].hazard for m in member_tuples if m[1] and m[1].hazard and m[1].hazard != "UNKNOWN"])
            common_eq = cls._most_frequent([m[1].equipment for m in member_tuples if m[1] and m[1].equipment and m[1].equipment != "UNKNOWN"])
            common_bar = cls._most_frequent([m[1].barrier for m in member_tuples if m[1] and m[1].barrier and m[1].barrier != "UNKNOWN"])
            common_lsr = cls._most_frequent([m[1].primary_life_saving_rule for m in member_tuples if m[1] and m[1].primary_life_saving_rule and m[1].primary_life_saving_rule != "UNKNOWN"])
            common_asset = cls._most_frequent([m[0].functional_location or m[0].site for m in member_tuples if m[0].functional_location or m[0].site])

            # Generate human-readable cluster name
            cluster_name = cls._generate_cluster_name(common_act, common_haz, common_eq, common_lsr)

            # Dates
            dates = [m[0].report_date for m in member_tuples if m[0].report_date]
            first_seen = datetime.combine(min(dates), datetime.min.time()).replace(tzinfo=timezone.utc) if dates else now
            last_seen = datetime.combine(max(dates), datetime.min.time()).replace(tzinfo=timezone.utc) if dates else now

            # Escalation Score & Explanation
            score, band, why_esc, metrics = EscalationEngine.calculate_cluster_escalation(member_tuples, now=now)

            if score >= 70.0:
                high_escalation_count += 1

            cluster = Cluster(
                cluster_name=cluster_name,
                common_mechanism=f"Hazard: {common_haz or 'General'} | Activity: {common_act or 'General'} | Barrier: {common_bar or 'General'}",
                common_asset=common_asset,
                common_hazard=common_haz,
                common_activity=common_act,
                common_equipment=common_eq,
                common_barrier=common_bar,
                common_lsr=common_lsr,
                recurrence_count=len(comp),
                escalation_score=score,
                escalation_band=band,
                systemic_pattern=json.dumps(why_esc),
                first_seen=first_seen,
                last_seen=last_seen,
            )
            db.add(cluster)
            await db.flush()

            # Add ClusterMembers
            for rid, sim in comp:
                db.add(ClusterMember(
                    cluster_id=cluster.id,
                    report_id=rid,
                    similarity_score=sim,
                ))

            # Create Pattern Escalation Alert if high escalation
            if score >= 60.0:
                alert_id = f"ALT-PAT-{cluster.id}"
                alert_reason = f"PATTERN ESCALATION ALERT: Cluster '{cluster_name}' reached escalation score {score} ({band.value}).\nWhy Escalating:\n" + "\n".join(why_esc)
                
                alert_stmt = select(Alert).where(Alert.alert_id == alert_id)
                alert_res = await db.execute(alert_stmt)
                existing_alert = alert_res.scalar_one_or_none()

                if not existing_alert:
                    db.add(Alert(
                        alert_id=alert_id,
                        alert_type=AlertType.PATTERN_ESCALATION,
                        cluster_id=cluster.id,
                        score=score,
                        priority=PriorityLevel.CRITICAL if score >= 85 else PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR,
                        reason=alert_reason,
                        evidence_report_ids=[m[0].report_id for m in member_tuples],
                        status="OPEN",
                    ))
                else:
                    existing_alert.score = score
                    existing_alert.reason = alert_reason

        await db.commit()

        logger.info(
            f"[ClusteringService] Cluster rebuild complete: {len(components)} clusters formed, "
            f"{high_escalation_count} high-escalation clusters."
        )

        return ClusterRebuildResponse(
            total_reports_processed=len(reports),
            total_clusters_formed=len(components),
            high_escalation_clusters=high_escalation_count,
            rebuilt_at=now,
        )

    @classmethod
    async def get_clusters(cls, db: AsyncSession) -> List[ClusterResponse]:
        """Returns all clusters sorted by escalation_score descending."""
        stmt = select(Cluster).order_by(Cluster.escalation_score.desc())
        res = await db.execute(stmt)
        clusters = res.scalars().all()
        return [ClusterResponse.model_validate(c) for c in clusters]

    @classmethod
    async def get_cluster_detail(cls, cluster_id: int, db: AsyncSession) -> Optional[ClusterDetailResponse]:
        """Returns detailed cluster information including member reports & timeline."""
        stmt = select(Cluster).options(
            selectinload(Cluster.members).selectinload(ClusterMember.report).selectinload(Report.safety_analysis)
        ).where(Cluster.id == cluster_id)
        res = await db.execute(stmt)
        cluster = res.scalar_one_or_none()

        if not cluster:
            return None

        # Build members list
        members_list: List[ClusterMemberResponse] = []
        member_reports = []

        for m in cluster.members:
            r = m.report
            sa = r.safety_analysis if r else None
            if r:
                member_reports.append((r, sa, m.similarity_score or 0.5))
                members_list.append(ClusterMemberResponse(
                    report_id=r.report_id,
                    report_date=r.report_date,
                    site=r.site,
                    functional_location=r.functional_location,
                    short_description=r.fixed_short_description or (r.narrative[:100] if r.narrative else ""),
                    sif_fpi_potential=sa.sif_fpi_potential if sa else None,
                    primary_life_saving_rule=sa.primary_life_saving_rule if sa else None,
                    priority_level=sa.priority_level if sa else None,
                    similarity_to_cluster=m.similarity_score or 0.5,
                ))

        # Sort members by date asc
        members_list.sort(key=lambda x: x.report_date or date.min)

        # Build timeline
        timeline: List[TimelineEvent] = []
        if member_reports:
            dates = [m[0].report_date for m in member_reports if m[0].report_date]
            first_d = min(dates) if dates else date.today()

            for r, sa, _ in member_reports:
                d = r.report_date or first_d
                days_from_first = (d - first_d).days
                timeline.append(TimelineEvent(
                    report_id=r.report_id,
                    report_date=d,
                    days_from_first=days_from_first,
                    title=r.fixed_short_description or r.report_id,
                    narrative_snippet=(r.narrative or "")[:120],
                    hazard=sa.hazard if sa else None,
                    barrier_condition=sa.barrier_condition.value if sa and sa.barrier_condition else None,
                    exposure=sa.exposure if sa else None,
                    sif_fpi_potential=sa.sif_fpi_potential if sa else None,
                ))
            timeline.sort(key=lambda x: x.days_from_first)

        pattern_str: Optional[str] = getattr(cluster, "systemic_pattern", None)
        why_esc = []
        if pattern_str:
            try:
                why_esc = json.loads(str(pattern_str))
            except Exception:
                why_esc = [str(pattern_str)]

        if not getattr(cluster, "escalation_band", None):
            setattr(cluster, "escalation_band", EscalationBand.LOW)

        base_data = ClusterResponse.model_validate(cluster).model_dump()
        return ClusterDetailResponse(
            **base_data,
            systemic_pattern=pattern_str,
            members=members_list,
            timeline=timeline,
            why_escalating=why_esc,
        )

    # ── Internal Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _generate_cluster_name(act: Optional[str], haz: Optional[str], eq: Optional[str], lsr: Optional[str]) -> str:
        """Generates evidence-backed cluster name from actual common fields."""
        part1 = act or eq or lsr or "Precursor Safety Event"
        part2 = haz or "Hazardous Condition"
        name = f"{part1.title()} — {part2.title()}"
        return name[:180]

    @staticmethod
    def _most_frequent(items: List[str]) -> Optional[str]:
        if not items:
            return None
        counts: Dict[str, int] = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return max(counts.items(), key=lambda x: x[1])[0]
