"use client";

import { useState } from "react";
import Link from "next/link";
import { TouchButton } from "@/components/TouchButton";
import { AudioPrompt } from "@/components/AudioPrompt";
import { AccessibilityControls } from "@/components/AccessibilityControls";

const WELCOME = {
  hi: "MediKiosk में आपका स्वागत है। कृपया अपनी भाषा चुनें और शुरू करें।",
  en: "Welcome to MediKiosk. Please select your language and press Start.",
};

export default function Home() {
  const [lang, setLang] = useState<"hi" | "en">("hi");

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-8 px-6 text-center">
      <AccessibilityControls />

      <div className="h-20 w-20 rounded-full bg-primary flex items-center justify-center" aria-hidden="true">
        <span className="text-3xl text-white font-bold">M</span>
      </div>

      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-primary">
          {lang === "hi" ? "स्वागत है" : "Welcome"}
        </h1>
        <p className="text-2xl text-gray-600">MediKiosk</p>
      </div>

      <AudioPrompt text={WELCOME[lang]} language={lang} />

      <div className="flex gap-4">
        <TouchButton
          variant={lang === "hi" ? "primary" : "secondary"}
          size="large"
          onClick={() => setLang("hi")}
        >
          हिंदी
        </TouchButton>
        <TouchButton
          variant={lang === "en" ? "primary" : "secondary"}
          size="large"
          onClick={() => setLang("en")}
        >
          English
        </TouchButton>
      </div>

      <Link href="/kiosk-session">
        <TouchButton variant="success" size="large">
          {lang === "hi" ? "परामर्श शुरू करें" : "Start Consultation"}
        </TouchButton>
      </Link>
    </main>
  );
}
