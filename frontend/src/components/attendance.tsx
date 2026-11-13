"use client";
import Link from "next/link";
import {
  ArrowRight,
  Camera,
  CameraOff,
  Check,
  ChevronRight,
  Download,
  Focus,
  LoaderCircle,
  Plus,
  ScanFace,
  ShieldCheck,
  Square,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { displayDate, formatTime, initials, localDate } from "@/lib/domain";
import {
  downloadRecords,
  post,
  QUALITY_MESSAGES,
  RecognitionResult,
} from "@/lib/api";
import { useCamera } from "@/lib/use-camera";
import { useRecognition } from "@/lib/use-recognition";
import { useApp } from "./provider";
import { Registration } from "./registration";
import { FaceOverlay } from "./face-overlay";
export function Attendance() {
  const { members, records, exports, preferences, notify, ready, refresh } =
    useApp();
  const [registering, setRegistering] = useState(false);
  const [running, setRunning] = useState(false);
  const [clock, setClock] = useState<Date | null>(null);
  const [exporting, setExporting] = useState(false);
  const camera = useCamera(running);
  const recognition = useRecognition(
    running && Boolean(camera.stream),
    camera.videoRef,
    camera.capture,
    onRecognition,
  );
  const today = clock ? localDate(clock) : "";
  const todayRecords = records.filter((record) => record.date === today);
  const presentIds = new Set(todayRecords.map((record) => record.memberId));
  const exportState = exports.find((state) => state.attendance_date === today);
  useEffect(() => {
    setClock(new Date());
    const timer = setInterval(() => setClock(new Date()), 1000);
    const hide = () => {
      if (document.visibilityState === "hidden") setRunning(false);
    };
    document.addEventListener("visibilitychange", hide);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", hide);
    };
  }, []);
  useEffect(() => {
    if (!ready) setRunning(false);
  }, [ready]);
  useEffect(() => {
    if (recognition.error) {
      setRunning(false);
      notify(recognition.error, "error");
    }
  }, [recognition.error, notify]);
  function onRecognition(value: RecognitionResult) {
    for (const event of value.events) {
      if (event.kind === "attendance_created") {
        notify(event.message);
        void refresh(true);
      } else if (event.kind === "attendance_already_exists") {
        notify(event.message, "info");
        void refresh(true);
      } else if (
        event.kind === "attendance_failed" ||
        event.kind === "excel_failed"
      ) {
        notify(event.message, "error");
        void refresh();
      }
    }
  }
  async function exportToday() {
    setExporting(true);
    try {
      await downloadRecords({ date: today });
      notify("Today’s Excel workbook is ready.");
    } catch (error) {
      notify(
        error instanceof Error ? error.message : "Could not prepare Excel.",
        "error",
      );
    } finally {
      setExporting(false);
    }
  }
  const faces = recognition.result?.faces ?? [];
  const activeFace = faces.find((face) => face.state === "created") ?? faces[0];
  let status = "Camera standby";
  if (running) {
    if (camera.error) status = "Camera unavailable";
    else if (camera.loading) status = "Opening camera";
    else if (recognition.connecting) status = "Connecting recognition";
    else if (!faces.length) status = "Step into the camera view";
    else if (!activeFace.quality.accepted)
      status =
        QUALITY_MESSAGES[activeFace.quality.reasons[0]] ??
        "Adjust your position";
    else if (activeFace.state === "created") status = "Attendance successful";
    else if (activeFace.state === "already_exists")
      status = "Already checked in today";
    else if (activeFace.state === "confirming") status = "Confirming identity";
    else if (activeFace.state === "no_gallery")
      status = "Register a member to get started";
    else if (["unknown", "ambiguous"].includes(activeFace.state))
      status = "Face not recognized";
    else if (activeFace.state === "tracking_ambiguous")
      status = "Keep faces apart for a clear view";
    else if (activeFace.state === "save_failed")
      status = "Could not save. Retrying shortly";
    else status = "Recognizing";
  }
  const successful = activeFace?.state === "created";
  const statistics = [
    {
      label: "Checked in today",
      value: todayRecords.length,
      icon: <span className="tiny-live-dot" />,
      note: todayRecords.length
        ? "A good day to be here."
        : "A fresh start. Ready when you are.",
    },
    {
      label: "Registered members",
      value: members.length,
      icon: <Users size={14} />,
      note: "Your familiar faces, in one place.",
    },
    {
      label: "Waiting to check in",
      value: members.filter((member) => !presentIds.has(member.id)).length,
      icon: <Focus size={14} />,
      note: "Every arrival has its moment.",
    },
  ];
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="page-eyebrow">Your daily overview</div>
          <h1 className="luminous">Every arrival matters.</h1>
          <p>One familiar face. One less thing to think about.</p>
        </div>
        <div className="page-heading-actions">
          <span className="date-label">
            {clock ? displayDate(today) : "Your attendance workspace"}
          </span>
          <button
            className="capsule"
            disabled={!ready}
            onClick={() => {
              setRunning(false);
              setRegistering(true);
            }}
          >
            <Plus size={14} /> Register member
          </button>
        </div>
      </div>
      <div className="stats-row">
        {statistics.map((stat, index) => (
          <div className="stat" key={stat.label}>
            <span>
              {stat.label} {stat.icon}
            </span>
            <strong>
              {ready ? String(stat.value).padStart(2, "0") : "—"}
              {index === 0 && <small>/ {members.length}</small>}
            </strong>
            <p>{stat.note}</p>
          </div>
        ))}
      </div>
      <div className="attendance-grid">
        <section className="camera-panel glass-panel">
          <div className="panel-heading">
            <span>
              <Camera size={15} /> Recognition studio
            </span>
            <span className="camera-mode-label">
              <ShieldCheck size={13} /> Live recognition
            </span>
          </div>
          <div
            className={
              "camera-stage " +
              (running ? "camera-running " : "") +
              (successful ? "camera-confirmed" : "")
            }
          >
            <div className="scan-grid" />
            <div className="stage-topline">
              <span>
                <i
                  className={running ? "status-dot" : "status-dot status-off"}
                />{" "}
                Browser camera
              </span>
              <span>
                {clock ? formatTime(clock.toISOString()) : "00:00:00"}
              </span>
            </div>
            <video
              ref={camera.videoRef}
              autoPlay
              muted
              playsInline
              className={
                "studio-video " + (preferences.mirrorCamera ? "mirrored" : "")
              }
            />
            {running && recognition.result && !recognition.result.stale && (
              <FaceOverlay
                result={recognition.result}
                mirror={preferences.mirrorCamera}
              />
            )}
            {(!running || !camera.stream) && (
              <div className="camera-placeholder">
                <CameraOff size={35} strokeWidth={1} />
                <h2>
                  {camera.loading
                    ? "Opening your camera…"
                    : camera.error
                      ? "Let’s reconnect."
                      : members.length
                        ? "Your camera. Your space."
                        : "Your first familiar face."}
                </h2>
                <p>
                  {camera.error ||
                    (members.length
                      ? "Turn on your webcam to recognize registered members."
                      : "Register your name, ID and three face samples to begin.")}
                </p>
                {camera.error && (
                  <button className="capsule" onClick={camera.retry}>
                    Retry camera
                  </button>
                )}
                {!members.length && ready && (
                  <button
                    className="capsule primary-capsule"
                    onClick={() => setRegistering(true)}
                  >
                    <Plus size={14} /> Create attendance profile
                  </button>
                )}
              </div>
            )}
            {camera.stream && preferences.showGuide && !faces.length && (
              <div className="registration-face-guide" />
            )}
            <div
              className={
                "recognition-status " +
                (successful ? "recognition-success" : "")
              }
              role="status"
            >
              {camera.loading || recognition.connecting ? (
                <LoaderCircle size={14} className="spin" />
              ) : successful ? (
                <Check size={14} />
              ) : (
                <span className="mini-status-dot" />
              )}
              {status}
            </div>
          </div>
          <div className="camera-controls">
            <div>
              {running ? (
                <button
                  className="capsule"
                  onClick={() => {
                    setRunning(false);
                    void refresh();
                  }}
                >
                  <Square size={12} /> Turn off camera
                </button>
              ) : (
                <button
                  className="capsule primary-capsule glow-capsule"
                  disabled={!ready || !members.length}
                  onClick={() => setRunning(true)}
                >
                  <Camera size={14} /> Turn on camera
                </button>
              )}
              <span className="camera-control-hint">
                Automatic check-in for registered faces
              </span>
            </div>
            <span className="camera-mode-label">
              <ScanFace size={13} /> YuNet + SFace
            </span>
          </div>
        </section>
        <aside className="recent-panel glass-panel">
          <div className="panel-heading">
            <span>Today’s arrivals</span>
            <span className="count-badge">{todayRecords.length}</span>
          </div>
          <div className="arrival-list">
            {!todayRecords.length ? (
              <div className="empty-arrivals">
                <div className="empty-orbit">
                  <Check size={24} strokeWidth={1} />
                  <i />
                </div>
                <h3>A little quiet, for now.</h3>
                <p>
                  Your check-ins will appear here.
                  <br />
                  Register, turn on the camera, and step into view.
                </p>
              </div>
            ) : (
              todayRecords.map((record) => {
                const member = members.find(
                  (item) => item.id === record.memberId,
                );
                return (
                  <div className="arrival-row" key={record.id}>
                    <span
                      className={"avatar avatar-" + (member?.color ?? "blue")}
                    >
                      {initials(record.name)}
                    </span>
                    <div>
                      <strong>{record.name}</strong>
                      <small>{record.memberId}</small>
                    </div>
                    <div className="arrival-time">
                      <time>{formatTime(record.recordedAt)}</time>
                      <small>
                        <i /> Present
                      </small>
                    </div>
                  </div>
                );
              })
            )}
          </div>
          <div className="recent-footer">
            <Link href="/records">
              View all records <ArrowRight size={13} />
            </Link>
            <button
              className="icon-button"
              aria-label="Export today to Excel"
              onClick={exportToday}
              disabled={!todayRecords.length || exporting}
            >
              {exporting ? (
                <LoaderCircle size={15} className="spin" />
              ) : (
                <Download size={15} />
              )}
            </button>
          </div>
        </aside>
      </div>
      <div className="attendance-bottom">
        <span>
          <ShieldCheck size={15} /> A familiar face only needs to check in once
          a day.
        </span>
        <Link href="/members">
          Manage your people <ChevronRight size={14} />
        </Link>
      </div>
      {exportState && (
        <div
          className={"excel-status excel-" + exportState.status}
          role="status"
        >
          <span>
            {exportState.status === "available"
              ? "Attendance saved. Excel is ready to download."
              : exportState.status === "synced"
                ? "Daily Excel file is up to date."
                : exportState.status === "pending"
                  ? "Attendance saved. Updating the daily Excel file…"
                  : "Attendance saved. Daily Excel update needs a retry."}
          </span>
          {exportState.status === "error" && (
            <button
              className="text-button"
              onClick={async () => {
                try {
                  await post("/exports/retry");
                  await refresh();
                } catch (error) {
                  notify(
                    error instanceof Error
                      ? error.message
                      : "Could not retry Excel update.",
                    "error",
                  );
                }
              }}
            >
              Retry Excel update
            </button>
          )}
        </div>
      )}
      {registering && <Registration onClose={() => setRegistering(false)} />}
    </>
  );
}
