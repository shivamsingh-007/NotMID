import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "MediKiosk — Clinician Console",
  description: "Clinical case review and documentation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-surface text-gray-900 min-h-screen flex">
        <Sidebar />
        <div className="flex-1 flex flex-col min-h-screen">
          <header className="h-14 border-b bg-white px-6 flex items-center justify-between">
            <h2 className="font-semibold text-primary">MediKiosk Clinical Platform</h2>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">Demo Hospital</span>
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-medium">DR</div>
            </div>
          </header>
          <main className="flex-1 p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
