"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "◌  Nurse station" },
  { href: "/doctor", label: "◇  Doctor review" },
  { href: "/worklist", label: "≡  Worklist" },
  { href: "/documents/review", label: "▤  Document review" },
  { href: "/patients", label: "○  Patients" },
  { href: "/alerts", label: "△  Alerts" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="clinical-sidebar">
      <div className="mk-wordmark">Medi<em>Kiosk</em></div>
      <div className="sidebar-context">Clinical workspace</div>
      <nav className="clinical-nav" aria-label="Clinical navigation">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              data-active={active}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
      <div className="sidebar-shift"><span>Shift handoff</span><strong>12:30 · 48 min</strong><span>3 handoffs still open</span></div>
    </aside>
  );
}
