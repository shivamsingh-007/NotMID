"use client";

import { useState } from "react";

export default function DoctorReviewPage() {
  const [reviewState, setReviewState] = useState<"editing" | "signed" | "rejected">("editing");
  const [assessment, setAssessment] = useState("Severely elevated blood pressure with exertional breathlessness. Needs repeat measurement and focused cardiovascular assessment.");
  const signed = reviewState === "signed";
  const rejected = reviewState === "rejected";

  return (
    <div>
      <header className="dashboard-heading mk-enter">
        <div><span className="mk-eyebrow">Doctor review · Evidence linked</span><h1 className="mk-display">Review before you sign.</h1><p>Patient-confirmed facts and source evidence remain visible beside the editable draft.</p></div>
        <span className={`mk-pill ${signed ? "mk-pill--success" : rejected ? "mk-pill--danger" : "mk-pill--warning"}`} role="status" aria-live="polite">{signed ? "Signed by Dr Rao" : rejected ? "Draft rejected · Not part of record" : "AI-assisted draft · Unsigned"}</span>
      </header>

      <div className="review-layout mk-enter">
        <aside className="mk-card patient-rail">
          <span className="mk-pill mk-pill--danger">Urgent review</span>
          <h2 className="patient-name">Asha Devi</h2><p className="patient-meta">MK-2048 · 54 yrs · Hindi</p>
          <div className="rail-list">
            <div className="rail-item"><span>Chief concern</span><strong>Breathlessness · 2 days</strong></div>
            <div className="rail-item"><span>Latest vitals</span><strong>BP 178/104 · SpO₂ 93%</strong></div>
            <div className="rail-item"><span>Known allergy</span><strong>Penicillin — rash</strong></div>
            <div className="rail-item"><span>Nurse handoff</span><strong>Repeat BP requested</strong></div>
          </div>
        </aside>

        <section className="mk-card draft-panel">
          <header className="draft-header"><span className="mk-pill mk-pill--warning">Draft v3 · model output</span><h1 className="mk-display">Clinical note</h1><p>Last autosaved 10:42 · Changes are not part of the medical record until signed.</p></header>
          <div className="draft-body">
            <div className="draft-section"><label htmlFor="history">History of presenting concern</label><textarea id="history" disabled={signed || rejected} defaultValue="Patient reports breathlessness on walking for two days, with mild headache. Denies chest pain. Symptoms were confirmed in Hindi during intake."/><span className="source-link">View 3 patient-confirmed sources ↗</span></div>
            <div className="draft-section"><label htmlFor="assessment">Assessment — clinician editable</label><textarea id="assessment" disabled={signed || rejected} value={assessment} onChange={(event) => setAssessment(event.target.value)}/><span className="source-link">Evidence: vitals + nurse handoff ↗</span></div>
            <div className="draft-section"><label htmlFor="plan">Plan</label><textarea id="plan" disabled={signed || rejected} defaultValue="Repeat BP manually. Complete examination. Escalate according to facility hypertension protocol if repeat remains severely elevated."/><span className="source-link">Facility protocol MK-HTN-04 ↗</span></div>
            <div className="signoff">
              <div><strong>{signed ? "Signed and locked" : rejected ? "Draft rejected" : "Clinician decision required"}</strong><p>{signed ? "Further changes require an addendum." : rejected ? "The generated text was not accepted and nothing was signed." : "Edit and sign, or reject the generated draft without adding it to the record."}</p></div>
              <div className="flex flex-wrap gap-2"><button className="mk-button mk-button--danger" disabled={signed || rejected} onClick={() => setReviewState("rejected")}>Reject draft</button><button className={`mk-button ${signed ? "mk-button--soft" : "mk-button--success"}`} disabled={signed || rejected} onClick={() => setReviewState("signed")}>{signed ? "Signed ✓" : "Review & sign"}</button></div>
            </div>
          </div>
        </section>

        <aside className="mk-card evidence-rail">
          <h2>Source evidence</h2>
          <article className="evidence-card"><span>Patient · 10:28 · confirmed</span><q>चलने पर सांस फूल रही है, दो दिन से।</q><span>Hindi transcript · high confidence</span></article>
          <article className="evidence-card"><span>Nurse Kavita · 10:36</span><q>Automated BP repeated manually; patient seated for five minutes.</q><span>Handoff note · staff attributed</span></article>
          <article className="evidence-card"><span>Vitals · 10:38</span><q>BP 178/104 mmHg, pulse 96, SpO₂ 93%.</q><span>Device import · verified</span></article>
          <article className="evidence-card"><span>Unresolved</span><q>Medication adherence was not captured.</q><span className="mk-pill mk-pill--warning">Ask patient</span></article>
        </aside>
      </div>
    </div>
  );
}
