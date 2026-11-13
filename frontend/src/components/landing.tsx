"use client";

import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCheck,
  Fingerprint,
  Focus,
  ScanFace,
  ShieldCheck,
  Table2,
  Users,
  Video,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { BrandMark, CircuitBoard, CornerLights, FaceMesh } from "./instruments";

const stages = ["Recognition", "Registration", "Attendance"];

export function Landing() {
  const [stage, setStage] = useState(0);
  const [detected, setDetected] = useState(false);
  const scene = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) =>
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        }),
      { threshold: 0.15 },
    );
    document
      .querySelectorAll(".reveal")
      .forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="landing-nav construction">
        <Link href="/" className="brand">
          <BrandMark small />
          <span>presence</span>
        </Link>
        <nav aria-label="Main navigation">
          <a href="#workflow">How it works</a>
          <a href="#workspace">The workspace</a>
        </nav>
        <Link className="capsule glow-capsule" href="/attendance">
          <span>Open workspace</span>
          <ArrowUpRight size={14} />
        </Link>
      </header>
      <main id="main">
        <section
          className="hero"
          onPointerMove={(event) => {
            if (event.pointerType !== "mouse") return;
            const bounds = event.currentTarget.getBoundingClientRect();
            scene.current?.style.setProperty(
              "--pointer-x",
              `${(event.clientX - bounds.left - bounds.width / 2) / 100}px`,
            );
          }}
          onPointerLeave={() =>
            scene.current?.style.setProperty("--pointer-x", "0px")
          }
        >
          <div className="spotlights" aria-hidden="true">
            <i />
            <i />
            <i />
          </div>
          <div className="hero-copy">
            <div className="ruled-eyebrow intro-enter">
              A moment is all it takes
            </div>
            <div className="wordmark-frame intro-enter">
              <CornerLights />
              <h1 className="wordmark">
                Presence<span className="wordmark-period">.</span>
              </h1>
              <span className="wordmark-cross cross-left">+</span>
              <span className="wordmark-cross cross-right">+</span>
            </div>
            <p className="hero-promise intro-enter">
              Show up. Be recognized.
              <br />
              <span>Attendance, without the interruption.</span>
            </p>
          </div>

          <div
            ref={scene}
            className={`product-fan stage-${stage} ${detected ? "is-detected" : ""}`}
          >
            <div className="fan-guide" aria-hidden="true" />
            <div className="fan-card member-preview">
              <div className="instrument-bar">
                <Users size={14} />
                <span>Your people</span>
                <span className="tiny-label">Ready</span>
              </div>
              <div className="mini-members">
                {[
                  ["·", "Your identity", "Full name & member ID"],
                  ["·", "Your face samples", "Three verified angles"],
                  ["·", "Your daily arrival", "One check-in per day"],
                  ["·", "Your records", "Ready for Excel"],
                ].map(([initial, name, role], i) => (
                  <div
                    className={`mini-member ${i === 1 ? "mini-selected" : ""}`}
                    key={name}
                  >
                    <span
                      className={`avatar avatar-${["blue", "lavender", "teal", "silver"][i]}`}
                    >
                      {initial}
                    </span>
                    <span>
                      {name}
                      <small>{role}</small>
                    </span>
                    <Check size={12} />
                  </div>
                ))}
              </div>
              <div className="mini-card-foot">
                <span className="status-dot" /> Ready to recognize
              </div>
            </div>
            <div className="fan-card scanner-preview">
              <div className="instrument-bar">
                <ScanFace size={14} />
                <span>{stages[stage]}</span>
                <span className="preview-live">
                  <i /> Workflow illustration
                </span>
              </div>
              <button
                className="hero-scan"
                aria-label={
                  detected
                    ? "Reset recognition preview"
                    : "Try recognition preview"
                }
                onClick={() => setDetected(!detected)}
              >
                <div className="scan-grid" />
                <div className="scan-orbit orbit-one" />
                <div className="scan-orbit orbit-two" />
                <FaceMesh />
                <div className="scan-target">
                  <i />
                  <i />
                  <i />
                  <i />
                </div>
                <div className="scan-beam" />
                <span className="face-coordinates">
                  x 0284
                  <br />y 0162
                </span>
                <span className="face-quality">
                  {detected ? "Preview ready" : "Tap to explore"}
                </span>
                {detected && (
                  <span className="recognized-label">
                    <Check size={12} /> Familiar face
                  </span>
                )}
              </button>
              <div className="scan-caption">
                <span
                  className={`status-dot ${detected ? "status-green" : ""}`}
                />
                <span>
                  {detected
                    ? "Your next arrival starts here"
                    : stage === 1
                      ? "Three angles. One familiar face."
                      : stage === 2
                        ? "Every arrival, accounted for."
                        : "A familiar face. A seamless check-in."}
                </span>
                <CheckCheck size={14} />
              </div>
            </div>
            <div className="fan-card activity-preview">
              <div className="instrument-bar">
                <Table2 size={14} />
                <span>Attendance log</span>
              </div>
              <div className="mini-log-title">
                <span>Today’s arrivals</span>
                <span>Present</span>
              </div>
              <div className="mini-log">
                <span className="avatar avatar-lavender">·</span>
                <div>
                  Your next arrival<small>Saved after recognition</small>
                </div>
                <span className="mini-time">
                  —
                  <small>
                    <i /> Ready
                  </small>
                </span>
              </div>
              <div className="log-confirmation">
                <div className="success-orb">
                  <Check size={18} />
                </div>
                <span>
                  Right here.
                  <br />
                  <strong>Right on record.</strong>
                </span>
              </div>
              <div className="mini-card-foot">
                <ShieldCheck size={12} /> One check-in per person, per day
              </div>
            </div>
          </div>

          <div className="hero-controls">
            <div
              className="segmented"
              role="tablist"
              aria-label="Preview workflow"
            >
              {stages.map((name, index) => (
                <button
                  role="tab"
                  aria-selected={stage === index}
                  key={name}
                  className={stage === index ? "active" : ""}
                  onClick={() => {
                    setStage(index);
                    setDetected(index === 2);
                  }}
                >
                  {name}
                </button>
              ))}
            </div>
            <span className="preview-note">
              A preview of a more present classroom.
            </span>
          </div>
          <div className="capability-strip">
            <span>
              <Video size={14} /> Webcam ready
            </span>
            <span>
              <Fingerprint size={14} /> Face-first check-in
            </span>
            <span>
              <ShieldCheck size={14} /> Duplicate prevention
            </span>
            <span>
              <Table2 size={14} /> Excel export
            </span>
          </div>
        </section>

        <section id="workflow" className="workflow-section chapter reveal">
          <div className="ruled-eyebrow">A thoughtful little workflow</div>
          <h2 className="luminous">
            Less taking attendance.
            <br />
            More being present.
          </h2>
          <p className="section-description">
            One camera connects your people to their attendance.
            <br className="desktop-break" /> Every step, in one considered
            workspace.
          </p>
          <CircuitBoard />
          <div className="workflow-steps">
            <div>
              <span>01</span>
              <h3>Meet your people</h3>
              <p>Register a name, an ID, and three face samples.</p>
            </div>
            <div>
              <span>02</span>
              <h3>Let the camera see</h3>
              <p>A familiar face becomes a confirmed identity.</p>
            </div>
            <div>
              <span>03</span>
              <h3>Keep a clear record</h3>
              <p>One daily check-in, ready to export.</p>
            </div>
          </div>
        </section>

        <section id="workspace" className="workspace-section chapter reveal">
          <div className="ruled-eyebrow">Your daily workspace</div>
          <h2 className="luminous">
            Everything in its place.
            <br />
            Everyone accounted for.
          </h2>
          <p className="section-description">
            A clear view of your camera, your members,
            <br className="desktop-break" /> and every check-in that follows.
          </p>
          <div className="feature-field">
            <Link href="/attendance" className="feature-tile">
              <div className="mini-instrument instrument-focus">
                <div className="focus-rings">
                  <Focus strokeWidth={0.7} />
                  <span className="focus-center">
                    <ScanFace strokeWidth={1.1} />
                  </span>
                  <i />
                </div>
              </div>
              <span>
                A space for every arrival <ArrowUpRight size={14} />
              </span>
            </Link>
            <Link href="/members" className="feature-tile">
              <div className="mini-instrument instrument-people">
                <span className="people-coin coin-back">
                  <Users size={24} strokeWidth={1} />
                </span>
                <span className="people-coin coin-front">
                  <Fingerprint size={37} strokeWidth={1} />
                </span>
                <div className="instrument-line" />
              </div>
              <span>
                Familiar faces, organized <ArrowUpRight size={14} />
              </span>
            </Link>
            <Link href="/records" className="feature-tile">
              <div className="mini-instrument instrument-records">
                <div className="record-stack stack-back" />
                <div className="record-stack stack-front">
                  <Table2 size={21} strokeWidth={1} />
                  <i />
                  <i />
                  <i />
                  <span>
                    <Check size={10} /> .xlsx
                  </span>
                </div>
              </div>
              <span>
                Records that go with you <ArrowUpRight size={14} />
              </span>
            </Link>
          </div>
        </section>

        <section className="closing-section chapter reveal">
          <div className="closing-rule">
            <CornerLights />
            <h2 className="luminous">Make room for presence.</h2>
          </div>
          <div className="conversion-pair">
            <Link href="/attendance" className="conversion-card">
              <CornerLights />
              <div className="closing-art">
                <div className="embossed-plaque">
                  <BrandMark />
                </div>
                <div className="closing-traces" />
              </div>
              <div>
                <h3>
                  Open the workspace <ArrowUpRight size={19} />
                </h3>
                <p>Step into your attendance workspace.</p>
              </div>
            </Link>
            <Link href="/members?register=true" className="conversion-card">
              <CornerLights />
              <div className="closing-art">
                <div className="embossed-medallion">
                  <Fingerprint size={57} strokeWidth={0.85} />
                </div>
                <div className="closing-traces" />
              </div>
              <div>
                <h3>
                  Meet your first member <ArrowUpRight size={19} />
                </h3>
                <p>Create your first attendance profile.</p>
              </div>
            </Link>
          </div>
          <Link href="/attendance" className="capsule closing-capsule">
            Take a closer look <ArrowRight size={14} />
          </Link>
        </section>
      </main>
      <footer className="landing-footer">
        <Link href="/" className="brand">
          <BrandMark small />
          <span>presence</span>
        </Link>
        <span>Built for the moments that count.</span>
        <span className="footer-preview">
          <i /> Face recognition attendance
        </span>
      </footer>
    </div>
  );
}
