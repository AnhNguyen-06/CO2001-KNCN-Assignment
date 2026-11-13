"use client";

import {
  Camera,
  Check,
  Database,
  Fingerprint,
  Monitor,
  RotateCcw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useState } from "react";
import { useApp } from "./provider";
import { Modal } from "./modal";

function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
}) {
  return (
    <button
      className={`toggle ${checked ? "toggle-on" : ""}`}
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={onChange}
    >
      <span />
    </button>
  );
}

export function Settings() {
  const {
    preferences,
    updatePreferences,
    resetPreferences,
    records,
    members,
    ready,
  } = useApp();
  const [confirmReset, setConfirmReset] = useState(false);
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="page-eyebrow">Make yourself at home</div>
          <h1 className="luminous">A workspace that feels like you.</h1>
          <p>A few thoughtful preferences for your daily flow.</p>
        </div>
        <span className="settings-saved">
          <Check size={13} /> Changes save automatically
        </span>
      </div>
      <div className="settings-layout">
        <div className="settings-main">
          <section className="settings-panel glass-panel">
            <div className="settings-section-heading">
              <Camera size={18} />
              <div>
                <h2>Your camera</h2>
                <p>Small adjustments to feel more natural on screen.</p>
              </div>
            </div>
            <div className="setting-row">
              <div>
                <h3>Mirror camera preview</h3>
                <p>See yourself the way you’re used to.</p>
              </div>
              <Toggle
                label="Mirror camera preview"
                checked={preferences.mirrorCamera}
                onChange={() =>
                  updatePreferences({ mirrorCamera: !preferences.mirrorCamera })
                }
              />
            </div>
            <div className="setting-row">
              <div>
                <h3>Face positioning guide</h3>
                <p>Show a subtle frame to help you find your place.</p>
              </div>
              <Toggle
                label="Face positioning guide"
                checked={preferences.showGuide}
                onChange={() =>
                  updatePreferences({ showGuide: !preferences.showGuide })
                }
              />
            </div>
          </section>
          <section className="settings-panel glass-panel">
            <div className="settings-section-heading">
              <Sparkles size={18} />
              <div>
                <h2>A little atmosphere</h2>
                <p>Keep the glow. Choose how much it moves.</p>
              </div>
            </div>
            <div className="setting-row">
              <div>
                <h3>Reduce ambient motion</h3>
                <p>Pause decorative light, radar, and circuit animations.</p>
              </div>
              <Toggle
                label="Reduce ambient motion"
                checked={preferences.reduceMotion}
                onChange={() =>
                  updatePreferences({ reduceMotion: !preferences.reduceMotion })
                }
              />
            </div>
            <p className="settings-footnote">
              Your operating system’s reduced-motion preference is also
              respected.
            </p>
          </section>
          <section className="settings-panel glass-panel">
            <div className="settings-section-heading">
              <Database size={18} />
              <div>
                <h2>Your attendance data</h2>
                <p>
                  Profiles and attendance are saved in the backend database.
                </p>
              </div>
            </div>
            <div className="data-counts">
              <span>
                <strong>{members.length}</strong> registered profiles
              </span>
              <span>
                <strong>{records.length}</strong> check-in records
              </span>
              <span className={ready ? "storage-healthy" : ""}>
                <i />
                {ready ? "Database connected" : "Database unavailable"}
              </span>
            </div>
            <div className="setting-row">
              <div>
                <h3>Restore preferences</h3>
                <p>
                  Restore camera and appearance preferences to their defaults.
                </p>
              </div>
              <button
                className="capsule reset-button"
                onClick={() => setConfirmReset(true)}
              >
                <RotateCcw size={13} /> Reset preferences
              </button>
            </div>
          </section>
        </div>
        <aside className="settings-aside">
          <div className="privacy-emblem">
            <ShieldCheck size={43} strokeWidth={1} />
          </div>
          <h2>Considered by design.</h2>
          <p>
            Camera access starts with your permission. Frames are processed by
            the recognition service and face embeddings stay in the database.
          </p>
          <div className="settings-fact">
            <Monitor size={15} />
            <span>Next.js workspace</span>
          </div>
          <div className="settings-fact">
            <Fingerprint size={15} />
            <span>YuNet + SFace recognition</span>
          </div>
          <div className="settings-fact">
            <Database size={15} />
            <span>Timezone · UTC+07:00</span>
          </div>
        </aside>
      </div>
      {confirmReset && (
        <Modal
          title="A fresh start?"
          description="This restores camera and appearance preferences. Your registered profiles and attendance remain saved."
          onClose={() => setConfirmReset(false)}
        >
          <div className="modal-actions">
            <button
              className="text-button"
              onClick={() => setConfirmReset(false)}
            >
              Keep my workspace
            </button>
            <button
              className="capsule primary-capsule"
              onClick={() => {
                resetPreferences();
                setConfirmReset(false);
              }}
            >
              <RotateCcw size={14} /> Reset preferences
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
