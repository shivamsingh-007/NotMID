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
      <body className="clinician-body">
        <div className="clinician-shell">
          <Sidebar />
          <div className="clinician-content">
            <header className="clinician-topbar">
              <div>
                <span className="mk-eyebrow">Community Medicine · Morning shift</span>
                <div className="facility-name">MediKiosk District Care Centre · Jaipur</div>
              </div>
              <div className="clinician-profile">
                <div className="profile-copy"><strong>Dr Meera Rao</strong><span>General Medicine · HPR verified</span></div>
                <div className="profile-avatar" aria-hidden="true">MR</div>
              </div>
            </header>
            <main className="clinician-main">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
