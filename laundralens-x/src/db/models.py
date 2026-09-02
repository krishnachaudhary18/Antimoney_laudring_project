"""
LaundraLens X — SQLAlchemy ORM models.
All 8 tables: transactions, accounts, customers, alerts, investigations,
evidence, findings, model_scores, case_memory.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, Numeric, String, Text, func
)
from sqlalchemy.orm import relationship

from src.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    customer_type = Column(String, nullable=False)  # individual, business
    occupation_or_business_category = Column(String)
    expected_activity_category = Column(String)  # salary, student, merchant, small_business
    geographic_region = Column(String)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    accounts = relationship("Account", back_populates="customer")


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False)
    account_type = Column(String)   # savings, current, business
    creation_date = Column(DateTime)
    segment = Column(String)        # retail, sme, corporate
    risk_profile = Column(String)   # low, medium, high
    status = Column(String)         # active, inactive, flagged
    home_region = Column(String)
    is_synthetic_suspicious = Column(Boolean, default=False)
    scenario_id = Column(String, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.sender_account_id", back_populates="sender")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.receiver_account_id", back_populates="receiver")
    alerts = relationship("Alert", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    sender_account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    receiver_account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String(3), default="INR")
    channel = Column(String)        # UPI, NEFT, RTGS, IMPS, CASH
    transaction_type = Column(String)  # credit, debit, transfer
    merchant_category = Column(String, nullable=True)
    location = Column(String, nullable=True)
    status = Column(String, default="completed")
    scenario_id = Column(String, nullable=True)
    ground_truth_pattern = Column(String, nullable=True)  # "synthetic_suspicious_pattern" or null
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sender = relationship("Account", foreign_keys=[sender_account_id], back_populates="sent_transactions")
    receiver = relationship("Account", foreign_keys=[receiver_account_id], back_populates="received_transactions")


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    priority_score = Column(Float, nullable=True)
    risk_band = Column(String, nullable=True)   # LOW, MEDIUM, HIGH, CRITICAL
    trigger_source = Column(String)              # rule_engine, ml_model, manual
    status = Column(String, default="open")      # open, in_investigation, closed
    summary = Column(Text, nullable=True)
    scenario_id = Column(String, nullable=True)

    # Relationships
    account = relationship("Account", back_populates="alerts")
    investigations = relationship("Investigation", back_populates="alert")


class Investigation(Base):
    __tablename__ = "investigations"

    case_id = Column(String, primary_key=True)
    alert_id = Column(String, ForeignKey("alerts.alert_id"), nullable=True)
    account_id = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="ALERT_CREATED")
    agent_version = Column(String, default="1.0.0")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    alert = relationship("Alert", back_populates="investigations")
    evidence = relationship("Evidence", back_populates="investigation")
    findings = relationship("Finding", back_populates="investigation")
    model_scores = relationship("ModelScore", back_populates="investigation", uselist=False)
    case_memory = relationship("CaseMemory", back_populates="investigation")
    decisions = relationship("CaseDecision", back_populates="investigation")


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("investigations.case_id"), nullable=False, index=True)
    evidence_type = Column(String)  # transaction, metric, behavior, graph, model
    account_id = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    source = Column(String)         # tool name that generated this
    value = Column(JSON)            # structured evidence value
    calculation = Column(Text, nullable=True)    # formula / computation shown
    explanation = Column(Text, nullable=True)    # human-readable explanation
    created_at = Column(DateTime, default=func.now())

    # Relationships
    investigation = relationship("Investigation", back_populates="evidence")


class Finding(Base):
    __tablename__ = "findings"

    finding_id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("investigations.case_id"), nullable=False, index=True)
    category = Column(String)       # flow, temporal, behavioral, graph, model
    severity = Column(String)       # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String, nullable=False)
    description = Column(Text)
    evidence_ids = Column(JSON)     # list of evidence_id references
    confidence_label = Column(String)  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=func.now())

    # Relationships
    investigation = relationship("Investigation", back_populates="findings")


class ModelScore(Base):
    __tablename__ = "model_scores"

    score_id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("investigations.case_id"), nullable=False, index=True)
    xgboost_score = Column(Float, nullable=True)
    isolation_score = Column(Float, nullable=True)
    autoencoder_score = Column(Float, nullable=True)
    behavior_signal = Column(Float, nullable=True)
    flow_signal = Column(Float, nullable=True)
    temporal_signal = Column(Float, nullable=True)
    graph_signal = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    risk_band = Column(String, nullable=True)
    shap_values = Column(JSON, nullable=True)
    counterfactual = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    investigation = relationship("Investigation", back_populates="model_scores")


class CaseMemory(Base):
    __tablename__ = "case_memory"

    memory_id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("investigations.case_id"), nullable=False, index=True)
    memory_type = Column(String)   # tool_call, finding, score, state_transition
    key = Column(String)
    value = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    investigation = relationship("Investigation", back_populates="case_memory")


class CaseDecision(Base):
    __tablename__ = "case_decisions"

    decision_id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("investigations.case_id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # FILE_SAR, REQUEST_INFO, ENHANCED_DILIGENCE, DISMISS_FALSE_POSITIVE
    analyst_id = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    escalation_status = Column(String, default="PENDING_MLRO_APPROVAL")
    disposition_timestamp = Column(DateTime, default=func.now())

    # Relationships
    investigation = relationship("Investigation", back_populates="decisions")

