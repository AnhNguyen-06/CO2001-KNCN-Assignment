"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  ArrowUpRight,
  CircleHelp,
  Menu,
  ScanFace,
  Settings2,
  Table2,
  Users,
  X,
} from "lucide-react";
import { BrandMark } from "./instruments";
import { Modal } from "./modal";
import { useApp } from "./provider";

const links = [
  { href: "/attendance", label: "Attendance", icon: ScanFace },
  { href: "/members", label: "Members", icon: Users },
  { href: "/records", label: "Records", icon: Table2 },
  { href: "/settings", label: "Settings", icon: Settings2 },
];

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const { ready, backendError, refresh } = useApp();
  return (
    <div className="workspace">
      <a href="#workspace-content" className="skip-link">
        Skip to content
      </a>
      <header className="workspace-nav">
        <Link href="/" className="brand">
          <BrandMark small />
          <span>presence</span>
          <span className="brand-divider" />
          <small>Workspace</small>
        </Link>
        <nav
          className={
            mobileOpen ? "workspace-links mobile-open" : "workspace-links"
          }
          aria-label="Workspace navigation"
        >
          {links.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={pathname === href ? "active" : ""}
              aria-current={pathname === href ? "page" : undefined}
              onClick={() => setMobileOpen(false)}
            >
              <Icon size={15} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="workspace-nav-end">
          <button
            className="icon-button help-button"
            aria-label="How to use Presence"
            onClick={() => setHelpOpen(true)}
          >
            <CircleHelp size={18} />
          </button>
          <span className="workspace-avatar" title="Attendance workspace">
            P
          </span>
          <button
            className="icon-button mobile-menu"
            aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>
      <div className="preview-banner">
        <span className="preview-banner-label">
          <span className="mini-status-dot" />{" "}
          {ready ? "Live attendance" : "Connecting service"}
        </span>
        <span>
          Register once. Recognize a familiar face. Keep a clear attendance
          record.
        </span>
        <button onClick={() => setHelpOpen(true)}>
          How it works <ArrowUpRight size={12} />
        </button>
      </div>
      {backendError && (
        <div className="storage-warning" role="alert">
          {backendError}{" "}
          <button className="text-button" onClick={() => void refresh()}>
            Retry connection
          </button>
        </div>
      )}
      <main id="workspace-content" className="workspace-main">
        {children}
      </main>
      <footer className="workspace-footer">
        <span>
          <BrandMark small /> A little less admin. A little more presence.
        </span>
        <span>
          Connected workspace <i /> UTC+07:00
        </span>
      </footer>
      {helpOpen && (
        <Modal
          title="A little tour of Presence"
          description="Your face-first attendance workspace."
          onClose={() => setHelpOpen(false)}
        >
          <div className="help-content">
            <div>
              <ScanFace />
              <section>
                <h3>Try a check-in</h3>
                <p>
                  Register your profile first, then turn on the camera in
                  Attendance. A recognized face checks in once per day.
                </p>
              </section>
            </div>
            <div>
              <Users />
              <section>
                <h3>Add someone new</h3>
                <p>
                  Enter your full name and unique ID. Capture front, slightly
                  left and slightly right photos, then review and save your
                  profile.
                </p>
              </section>
            </div>
            <div>
              <Table2 />
              <section>
                <h3>Take your records along</h3>
                <p>
                  Search and filter attendance records, then download an Excel
                  workbook from the backend database.
                </p>
              </section>
            </div>
            <p className="help-note">
              Use good lighting and keep your face inside the frame. Your name,
              ID and face embeddings are saved after registration. Camera frames
              are processed in memory.
            </p>
          </div>
          <button
            className="capsule primary-capsule modal-done"
            onClick={() => setHelpOpen(false)}
          >
            Got it <ArrowUpRight size={14} />
          </button>
        </Modal>
      )}
    </div>
  );
}
