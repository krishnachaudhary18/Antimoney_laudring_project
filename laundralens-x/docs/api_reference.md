# LaundraLens X — REST API Reference Guide

Base URL: `http://127.0.0.1:8000/api/v1`  
Interactive OpenAPI Swagger Docs: `http://127.0.0.1:8000/api/docs`

---

## 1. System Health
### `GET /health`
Returns system operational state, timestamp, and active service name.
```json
{
  "status": "ok",
  "service": "LaundraLens X",
  "version": "1.0.0",
  "timestamp": "2026-09-03T03:30:00.000Z"
}
```

---

## 2. Alerts Queue & Triage
### `GET /alerts`
Lists all triaged alerts sorted by `priority_score` descending.
### `GET /alerts/{alert_id}`
Retrieves metadata and trigger summary for a specific alert.
### `PATCH /alerts/{alert_id}/status?status={status}`
Updates alert status (`open`, `in_review`, `resolved`, `escalated`, `dismissed`).

---

## 3. Autonomous Investigations
### `POST /investigations`
Executes an end-to-end 11-step investigation for a given alert in < 1.0s.
**Request:**
```json
{
  "alert_id": "ALERT-SCENARIO-001"
}
```
**Response:**
```json
{
  "case_id": "CASE-6713F954",
  "account_id": "ACC-B-001",
  "status": "REPORT_READY",
  "priority_score": 63.2,
  "risk_band": "HIGH",
  "signals": {
    "flow": 0.815,
    "temporal": 0.587,
    "behavior": 0.0,
    "graph": 0.147
  },
  "duration_seconds": 0.68,
  "findings_count": 3,
  "evidence_count": 3
}
```
### `GET /investigations/{case_id}`
Returns the current investigation state, diagnostic summary, and signal metrics.
### `GET /investigations/{case_id}/evidence`
Returns the complete forensic evidence ledger with exact calculations.
### `GET /investigations/{case_id}/timeline`
Returns the chronological transaction event sequence with flow indicators.
### `GET /investigations/{case_id}/counterfactual`
Returns What-If score sensitivity deltas.

---

## 4. Cases & Formal Reporting
### `GET /cases/{case_id}`
Returns case overview, findings taxonomy, and report summary.
### `POST /cases/{case_id}/report`
Compiles an evidence-grounded investigation report using Google Gemini Flash (with deterministic fallback).
### `GET /cases/{case_id}/dossier`
Returns a print-ready, formal regulatory **FIU-IND HTML SAR Dossier** with a SHA-256 cryptographic provenance hash.

---

## 5. Graph Intelligence & Forensics
### `GET /graph/{account_id}?hops=2`
Generates an interactive Pyvis HTML graph embedded directly into web clients.
### `GET /graph/{account_id}/neighbors?direction=both`
Returns immediate 1-hop in/out transactional neighbors.
### `GET /graph/syndicates/detect`
Discovers circular round-tripping cycles and bipartite funnel smurfing networks across the entire transaction database.

---

## 6. Real-Time Streaming
### `GET /stream/transactions`
Server-Sent Events (SSE) live event stream generating real-time payment transactions.
### `GET /stream/recent?limit=15`
Returns recent buffered transactions from the sliding-window buffer.

---

## 7. Compliance Officer Dispositions
### `POST /decisions`
Records an official human compliance determination on a case.
**Request:**
```json
{
  "case_id": "CASE-6713F954",
  "action": "FILE_SAR",
  "analyst_id": "OFFICER-7429",
  "reason_code": "TYP-01: Rapid Passthrough Layering",
  "notes": "97% conservation ratio and 58-minute velocity verified."
}
```
### `GET /decisions/{case_id}`
Returns the complete human decision audit log for a case.
