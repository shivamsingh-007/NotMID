"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/worklist", label: "Worklist" },
  { href: "/patients", label: "Patients" },
  { href: "/alerts", label: "Alerts" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-primary text-white min-h-screen flex flex-col">
      <div className="px-4 py-5 border-b border-white/20">
        <span className="font-bold text-lg">MediKiosk</span>
      </div>
      <nav className="flex-1 py-4 space-y-1 px-2">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`block px-3 py-2 rounded text-sm font-medium transition-colors ${
                active ? "bg-white/20" : "hover:bg-white/10"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
