"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const translations = {
  en: {
    title: "Welcome to MediKiosk",
    subtitle: "Please select your language and tap Start to begin.",
    start_button: "Start Consultation",
    language_label: "Your Language",
    device_info:
      "This kiosk session will automatically expire after 5 minutes of inactivity for your privacy.",
  },
  hi: {
    title: "MediKiosk में आपका स्वागत है",
    subtitle: "कृपया अपनी भाषा चुनें और शुरू करने के लिए Start दबाएं।",
    start_button: "परामर्श शुरू करें",
    language_label: "आपकी भाषा",
    device_info:
      "आपकी गोपनीयता के लिए, यह kiosk सत्र निष्क्रियता के 5 मिनट बाद स्वचालित रूप से समाप्त हो जाएगा।",
  },
};

export default function KioskSessionPage() {
  const router = useRouter();
  const [lang, setLang] = useState<"en" | "hi">("hi");
  const t = translations[lang];

  const handleStart = () => {
    // TODO: POST /api/v1/auth/kiosk/session then redirect to /consent
    router.push("/consent");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary to-primary/90 flex items-center justify-center p-8">
      <div className="max-w-lg w-full">
        <div className="bg-white rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-8">
            <div className="text-5xl mb-4">🏥</div>
            <h1 className="text-3xl font-bold text-primary mb-2">{t.title}</h1>
            <p className="text-gray-600">{t.subtitle}</p>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t.language_label}
            </label>
            <div className="flex gap-3">
              <button
                onClick={() => setLang("hi")}
                className={`flex-1 py-3 rounded-xl font-semibold text-lg transition ${
                  lang === "hi"
                    ? "bg-primary text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                हिंदी
              </button>
              <button
                onClick={() => setLang("en")}
                className={`flex-1 py-3 rounded-xl font-semibold text-lg transition ${
                  lang === "en"
                    ? "bg-primary text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                English
              </button>
            </div>
          </div>

          <button
            onClick={handleStart}
            className="w-full bg-accent text-white py-5 rounded-xl text-xl font-bold hover:bg-accent/90 transition min-h-[64px] mb-4"
          >
            {t.start_button}
          </button>

          <p className="text-xs text-gray-500 text-center">{t.device_info}</p>
        </div>
      </div>
    </div>
  );
}
