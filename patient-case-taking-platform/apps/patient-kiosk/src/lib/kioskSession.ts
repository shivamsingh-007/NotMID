import { createDemoPatientSession } from "./patientPortal";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface KioskSession {
  sessionId: string;
  encounterId: string;
  language: "hi" | "en";
}

export async function startLocalKioskSession(
  language: "hi" | "en",
): Promise<KioskSession> {
  const patient = await createDemoPatientSession();
  const query = new URLSearchParams({
    facility_id: patient.facilityId,
    device_id: "medikiosk-local-browser",
    language,
  });
  const response = await fetch(`${API_URL}/api/v1/auth/kiosk/session?${query}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Kiosk session is unavailable. Enable local demo routes.");
  }
  const payload = (await response.json()) as { session_id?: string };
  if (!payload.session_id) throw new Error("Kiosk session returned no identifier");
  const session = {
    sessionId: payload.session_id,
    encounterId: crypto.randomUUID(),
    language,
  };
  localStorage.setItem("notmid-kiosk-session-id", session.sessionId);
  localStorage.setItem("notmid-encounter-id", session.encounterId);
  localStorage.setItem("notmid-language", language);
  return session;
}
