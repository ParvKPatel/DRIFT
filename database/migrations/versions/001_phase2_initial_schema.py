"""Phase 2 initial schema migration

Revision ID: 001_phase2_initial_schema
Revises: 
Create Date: 2026-09-02 16:53:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_phase2_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pgvector extension if available
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception:
        pass  # Ignore if vector extension cannot be created in local non-pgvector test environment

    # 2. Create Enums
    evidence_status_enum = sa.Enum('EXPLICIT', 'INFERRED', 'UNKNOWN', name='evidence_status_enum')
    sif_decision_enum = sa.Enum('YES', 'NO', 'UNCERTAIN', name='sif_decision_enum')
    barrier_condition_enum = sa.Enum('INTACT', 'DEGRADED', 'FAILED', 'ABSENT', 'UNKNOWN', name='barrier_condition_enum')
    priority_level_enum = sa.Enum('ROUTINE', 'SAFETY_REVIEW', 'HIGH_PRIORITY_SIF_FPI_PRECURSOR', 'CRITICAL', 'UNCERTAIN', name='priority_level_enum')
    energy_source_enum = sa.Enum('MECHANICAL', 'KINETIC', 'GRAVITATIONAL', 'PRESSURE', 'ELECTRICAL', 'THERMAL', 'CHEMICAL', 'HYDROCARBON', 'STORED_ENERGY', 'VEHICLE_MOTION', 'UNKNOWN', name='energy_source_enum')
    alert_type_enum = sa.Enum('SIF_REVIEW', 'PATTERN_ESCALATION', 'BARRIER_WEAKNESS', 'NOVEL_CASE', 'REPORTING_ANOMALY', name='alert_type_enum')
    provenance_type_enum = sa.Enum('SYNTHETIC', 'REFERENCE', 'OIL_EXPORT', 'OTHER', name='provenance_type_enum')

    evidence_status_enum.create(op.get_bind(), checkfirst=True)
    sif_decision_enum.create(op.get_bind(), checkfirst=True)
    barrier_condition_enum.create(op.get_bind(), checkfirst=True)
    priority_level_enum.create(op.get_bind(), checkfirst=True)
    energy_source_enum.create(op.get_bind(), checkfirst=True)
    alert_type_enum.create(op.get_bind(), checkfirst=True)
    provenance_type_enum.create(op.get_bind(), checkfirst=True)

    # 3. Create 'reports' table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=False),
        sa.Column('source_system_id', sa.String(length=100), nullable=True),
        sa.Column('report_date', sa.Date(), nullable=True),
        sa.Column('report_time', sa.Time(), nullable=True),
        sa.Column('site', sa.String(length=150), nullable=True),
        sa.Column('unit', sa.String(length=150), nullable=True),
        sa.Column('shift', sa.String(length=50), nullable=True),
        sa.Column('functional_location', sa.String(length=200), nullable=True),
        sa.Column('functional_location_description', sa.Text(), nullable=True),
        sa.Column('item_no', sa.String(length=100), nullable=True),
        sa.Column('incident_type', sa.String(length=100), nullable=True),
        sa.Column('incident_sub_type', sa.String(length=100), nullable=True),
        sa.Column('incident_cause', sa.String(length=200), nullable=True),
        sa.Column('fixed_short_description', sa.Text(), nullable=True),
        sa.Column('line_item', sa.String(length=50), nullable=True),
        sa.Column('narrative', sa.Text(), nullable=False),
        sa.Column('corrective_action', sa.Text(), nullable=True),
        sa.Column('preventive_action', sa.Text(), nullable=True),
        sa.Column('man_hours', sa.Float(), nullable=True),
        sa.Column('lost_time', sa.Float(), nullable=True),
        sa.Column('operational_time_lost', sa.Float(), nullable=True),
        sa.Column('financial_implication', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=True),
        sa.Column('affected_person_type', sa.String(length=50), nullable=True),
        sa.Column('employee_or_contractor', sa.String(length=50), nullable=True),
        sa.Column('designation', sa.String(length=100), nullable=True),
        sa.Column('contractor_name', sa.String(length=150), nullable=True),
        sa.Column('actual_outcome', sa.String(length=150), nullable=True),
        sa.Column('source_file', sa.String(length=255), nullable=True),
        sa.Column('source_row_number', sa.Integer(), nullable=True),
        sa.Column('provenance', provenance_type_enum, server_default='OIL_EXPORT', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id')
    )
    op.create_index('ix_reports_id', 'reports', ['id'])
    op.create_index('ix_reports_report_id', 'reports', ['report_id'])
    op.create_index('ix_reports_site', 'reports', ['site'])
    op.create_index('ix_reports_unit', 'reports', ['unit'])
    op.create_index('ix_reports_functional_location', 'reports', ['functional_location'])
    op.create_index('ix_reports_incident_type', 'reports', ['incident_type'])
    op.create_index('ix_reports_incident_cause', 'reports', ['incident_cause'])
    op.create_index('idx_reports_site_date', 'reports', ['site', 'report_date'])

    # 4. Create 'safety_analysis' table
    op.create_table(
        'safety_analysis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=False),
        sa.Column('activity', sa.String(length=200), nullable=True),
        sa.Column('equipment', sa.String(length=200), nullable=True),
        sa.Column('hazard', sa.Text(), nullable=True),
        sa.Column('energy_source', energy_source_enum, nullable=True),
        sa.Column('exposure', sa.Text(), nullable=True),
        sa.Column('exposure_location', sa.String(length=200), nullable=True),
        sa.Column('barrier', sa.String(length=150), nullable=True),
        sa.Column('barrier_condition', barrier_condition_enum, nullable=True),
        sa.Column('potential_consequence', sa.Text(), nullable=True),
        sa.Column('sif_fpi_potential', sif_decision_enum, nullable=True),
        sa.Column('sif_confidence', sa.Float(), nullable=True),
        sa.Column('evidence_status', evidence_status_enum, nullable=True),
        sa.Column('evidence_span', sa.Text(), nullable=True),
        sa.Column('reason_code', sa.String(length=100), nullable=True),
        sa.Column('life_saving_rule', sa.String(length=50), nullable=True),
        sa.Column('novelty_score', sa.Float(), nullable=True),
        sa.Column('review_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('review_reason', sa.Text(), nullable=True),
        sa.Column('sif_evidence_score', sa.Float(), nullable=True),
        sa.Column('barrier_score', sa.Float(), nullable=True),
        sa.Column('recurrence_score', sa.Float(), nullable=True),
        sa.Column('escalation_score', sa.Float(), nullable=True),
        sa.Column('priority_score', sa.Float(), nullable=True),
        sa.Column('priority_level', priority_level_enum, nullable=True),
        sa.Column('analysis_version', sa.String(length=50), server_default='1.0.0', nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id')
    )
    op.create_index('ix_safety_analysis_id', 'safety_analysis', ['id'])
    op.create_index('ix_safety_analysis_report_id', 'safety_analysis', ['report_id'])

    # 5. Create 'evidence' table
    op.create_table(
        'evidence',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=True),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('evidence_text', sa.Text(), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=True),
        sa.Column('end_offset', sa.Integer(), nullable=True),
        sa.Column('evidence_status', evidence_status_enum, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['safety_analysis.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evidence_id', 'evidence', ['id'])
    op.create_index('ix_evidence_report_id', 'evidence', ['report_id'])

    # 6. Create 'report_embeddings' table
    op.create_table(
        'report_embeddings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_report_embeddings_id', 'report_embeddings', ['id'])
    op.create_index('ix_report_embeddings_report_id', 'report_embeddings', ['report_id'])

    # 7. Create 'similar_reports' table
    op.create_table(
        'similar_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=False),
        sa.Column('similar_report_id', sa.String(length=100), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['similar_report_id'], ['reports.report_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id', 'similar_report_id', name='uq_similar_report_pair')
    )
    op.create_index('ix_similar_reports_id', 'similar_reports', ['id'])
    op.create_index('ix_similar_reports_report_id', 'similar_reports', ['report_id'])

    # 8. Create 'clusters' table
    op.create_table(
        'clusters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cluster_name', sa.String(length=200), nullable=False),
        sa.Column('common_asset', sa.String(length=150), nullable=True),
        sa.Column('common_hazard', sa.String(length=200), nullable=True),
        sa.Column('common_activity', sa.String(length=200), nullable=True),
        sa.Column('common_barrier', sa.String(length=150), nullable=True),
        sa.Column('recurrence_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('escalation_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('systemic_pattern', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clusters_id', 'clusters', ['id'])

    # 9. Create 'cluster_members' table
    op.create_table(
        'cluster_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cluster_id', 'report_id', name='uq_cluster_member')
    )
    op.create_index('ix_cluster_members_id', 'cluster_members', ['id'])
    op.create_index('ix_cluster_members_cluster_id', 'cluster_members', ['cluster_id'])
    op.create_index('ix_cluster_members_report_id', 'cluster_members', ['report_id'])

    # 10. Create 'alerts' table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_id', sa.String(length=100), nullable=False),
        sa.Column('alert_type', alert_type_enum, nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('priority', priority_level_enum, nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence_report_ids', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='OPEN', nullable=False),
        sa.Column('reviewer_decision', sa.String(length=100), nullable=True),
        sa.Column('reviewer_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alert_id')
    )
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_alert_id', 'alerts', ['alert_id'])
    op.create_index('ix_alerts_status', 'alerts', ['status'])

    # 11. Create 'reviews' table
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.String(length=100), nullable=True),
        sa.Column('alert_id', sa.Integer(), nullable=True),
        sa.Column('reviewer_id', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=100), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reviews_id', 'reviews', ['id'])


def downgrade() -> None:
    op.drop_table('reviews')
    op.drop_table('alerts')
    op.drop_table('cluster_members')
    op.drop_table('clusters')
    op.drop_table('similar_reports')
    op.drop_table('report_embeddings')
    op.drop_table('evidence')
    op.drop_table('safety_analysis')
    op.drop_table('reports')

    bind = op.get_bind()
    sa.Enum(name='provenance_type_enum').drop(bind, checkfirst=True)
    sa.Enum(name='alert_type_enum').drop(bind, checkfirst=True)
    sa.Enum(name='energy_source_enum').drop(bind, checkfirst=True)
    sa.Enum(name='priority_level_enum').drop(bind, checkfirst=True)
    sa.Enum(name='barrier_condition_enum').drop(bind, checkfirst=True)
    sa.Enum(name='sif_decision_enum').drop(bind, checkfirst=True)
    sa.Enum(name='evidence_status_enum').drop(bind, checkfirst=True)
