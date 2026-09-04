export type SummaryStatus = "draft" | "in_review" | "rejected" | "signed" | "superseded";

export type SummaryContent = {
  chief_complaint: string;
  history_of_present_illness: string[];
  relevant_negatives: string[];
  document_facts: string[];
  red_flags: string[];
  uncertainties: string[];
};

export type EvidenceLink = {
  output_path: string;
  source_path: string;
  source_type: "patient_response" | "document" | "deterministic_rule";
};

export type SummaryRecord = {
  id: string;
  tenant_id: string;
  facility_id: string;
  patient_id: string;
  encounter_id: string;
  lineage_id: string;
  generation: number;
  parent_summary_id: string | null;
  status: SummaryStatus;
  content: SummaryContent;
  evidence: EvidenceLink[];
  confidence: { score: number; basis: string; not_clinical_probability: true };
  provider: "mock" | "template-fallback";
  degraded: boolean;
  lock_version: number;
  updated_at: string;
  signature_sha256: string | null;
  rejection_reason: string | null;
};

export class SummaryApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function accessToken(): string {
  const token = window.sessionStorage.getItem("medikiosk.access_token");
  if (!token) {
    throw new SummaryApiError("Clinical session unavailable. Sign in again to review summaries.", 401);
  }
  return token;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}/api/v1/summary-workflows${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken()}`,
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new SummaryApiError(
      payload?.detail ?? "The clinical summary service is unavailable.",
      response.status,
    );
  }
  return (await response.json()) as T;
}

export function listSummaries(encounterId: string): Promise<SummaryRecord[]> {
  return request(`?encounter_id=${encodeURIComponent(encounterId)}`);
}

export function saveDraft(summary: SummaryRecord, content: SummaryContent) {
  return request<SummaryRecord>(`/${summary.id}/draft`, {
    method: "PATCH",
    body: JSON.stringify({ expected_version: summary.lock_version, content }),
  });
}

export function submitForReview(summary: SummaryRecord) {
  return request<SummaryRecord>(`/${summary.id}/submit-review`, {
    method: "POST",
    body: JSON.stringify({ expected_version: summary.lock_version }),
  });
}

export function rejectSummary(summary: SummaryRecord, reason: string) {
  return request<SummaryRecord>(`/${summary.id}/reject`, {
    method: "POST",
    body: JSON.stringify({ expected_version: summary.lock_version, reason }),
  });
}

export function regenerateSummary(summary: SummaryRecord) {
  return request<SummaryRecord>(`/${summary.id}/regenerate`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      facility_id: summary.facility_id,
      patient_id: summary.patient_id,
      encounter_id: summary.encounter_id,
      language: "en",
      expected_version: summary.lock_version,
    }),
  });
}

export function signSummary(summary: SummaryRecord) {
  return request<SummaryRecord>(`/${summary.id}/sign`, {
    method: "POST",
    body: JSON.stringify({ expected_version: summary.lock_version }),
  });
}
