"use client";

import Link from "next/link";
import { useState } from "react";

const queue = [
  { id: "MK-2048", name: "Asha Devi", meta: "54 yrs · Hindi", priority: "Urgent", tone: "danger", bp: "178/104", spo2: "93%", handoff: "Doctor requested" },
  { id: "MK-2051", name: "Rakesh Kumar", meta: "42 yrs · Hinglish", priority: "Review", tone: "warning", bp: "146/92", spo2: "97%", handoff: "Vitals complete" },
  { id: "MK-2054", name: "Farida Begum", meta: "31 yrs · Hindi", priority: "Routine", tone: "success", bp: "118/76", spo2: "98%", handoff: "Intake in progress" },
];

export default function Dashboard() {
  const [filter, setFilter] = useState<"All" | "Urgent">("All");
  const visibleQueue = filter === "Urgent" ? queue.filter((patient) => patient.priority === "Urgent") : queue;

  return (
    <div>
      <header className="dashboard-heading mk-enter">
        <div><span className="mk-eyebrow">Nurse station · नर्स डेस्क</span><h1 className="mk-display">Good morning, Kavita.</h1><p>Three patients need your attention before the next handoff.</p></div>
        <button className="mk-button mk-button--soft">＋ Register walk-in</button>
      </header>

      <section className="metric-grid mk-enter" aria-label="Shift overview">
        <article className="mk-card metric-card" data-tone="danger"><span>Urgent now</span><strong>1</strong></article>
        <article className="mk-card metric-card" data-tone="warning"><span>Awaiting vitals</span><strong>3</strong></article>
        <article className="mk-card metric-card" data-tone="success"><span>Handoffs ready</span><strong>4</strong></article>
        <article className="mk-card metric-card"><span>Seen this shift</span><strong>18</strong></article>
      </section>

      <div className="clinical-grid mk-enter">
        <section className="mk-card panel">
          <header className="panel-header">
            <div><h2>Live triage queue</h2><p>Ordered by deterministic urgency, then waiting time</p></div>
            <div className="filter-row">
              {(["All", "Urgent"] as const).map((item) => <button key={item} className="filter-button" aria-pressed={filter === item} onClick={() => setFilter(item)}>{item}</button>)}
            </div>
          </header>
          {visibleQueue.map((patient) => (
            <article className="queue-row" key={patient.id}>
              <div className="patient-cell"><strong>{patient.name}</strong><span>{patient.id} · {patient.meta}</span></div>
              <span className={`mk-pill mk-pill--${patient.tone}`}>{patient.priority}</span>
              <div className="vitals-cell"><div><small>BP</small><strong>{patient.bp}</strong></div><div><small>SpO₂</small><strong>{patient.spo2}</strong></div></div>
              <div><div className="handoff-cell">{patient.handoff}</div><Link className="queue-action" href="/doctor">Open handoff →</Link></div>
            </article>
          ))}
        </section>

        <aside className="mk-card panel">
          <header className="panel-header"><div><h2>Needs action</h2><p>Rules-owned alerts and handoffs</p></div><span className="mk-pill mk-pill--danger">2 open</span></header>
          <div className="alert-list">
            <article className="alert-card" data-tone="danger"><span className="alert-rule">Urgent symptom rule</span><strong>High BP with breathlessness</strong><p>Asha Devi · confirm repeat BP and notify duty doctor now.</p><button className="filter-button">Acknowledge</button></article>
            <article className="alert-card"><span className="alert-rule">Workflow alert</span><strong>Handoff due in 12 min</strong><p>Rakesh Kumar · vitals complete, summary needs nurse note.</p><button className="filter-button">Add handoff note</button></article>
            <article className="alert-card"><span className="alert-rule">Queue health</span><strong>Room 03 is available</strong><p>Move the next routine patient when ready.</p></article>
          </div>
        </aside>
      </div>
    </div>
  );
}
