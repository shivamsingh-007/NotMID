const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function synthesizePrompt(
  text: string,
  language: "hi" | "en",
): Promise<Blob> {
  const response = await fetch(`${API_URL}/api/v1/tts/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language, voice: "calm" }),
  });
  if (!response.ok) {
    throw new Error("Mock voice is temporarily unavailable");
  }
  if (!response.headers.get("content-type")?.startsWith("audio/wav")) {
    throw new Error("Mock voice returned an invalid audio type");
  }
  return response.blob();
}
