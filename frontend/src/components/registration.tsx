"use client";
import {
  Camera,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleUserRound,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useCamera } from "@/lib/use-camera";
import { ApiError, post, QUALITY_MESSAGES } from "@/lib/api";
import { useApp } from "./provider";
import { Modal } from "./modal";
const angles = [
  "Look straight ahead",
  "Turn slightly left",
  "Turn slightly right",
];
export function Registration({ onClose }: { onClose: () => void }) {
  const { addMember, members, preferences, ready } = useApp();
  const [step, setStep] = useState(0);
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [samples, setSamples] = useState<string[]>([]);
  const [cameraOn, setCameraOn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const mounted = useRef(true);
  const request = useRef<AbortController | null>(null);
  const captureLock = useRef(false);
  const camera = useCamera(step === 1 && cameraOn);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      request.current?.abort();
    };
  }, []);
  function continueToCapture(event: React.FormEvent) {
    event.preventDefault();
    if (!id.trim() || !name.trim()) {
      setError("Enter a member ID and full name.");
      return;
    }
    if (members.some((member) => member.id === id.trim())) {
      setError("This member ID is already registered.");
      return;
    }
    setError("");
    setStep(1);
  }
  async function capture() {
    if (samples.length >= 3 || captureLock.current) return;
    const photo = camera.capture();
    if (!photo) {
      setError("Wait for the camera preview before capturing.");
      return;
    }
    captureLock.current = true;
    setBusy(true);
    setError("");
    const controller = new AbortController();
    request.current = controller;
    try {
      await post("/registration/sample", { image: photo }, controller.signal);
      if (mounted.current) setSamples((previous) => [...previous, photo]);
    } catch (error) {
      if (!mounted.current || controller.signal.aborted) return;
      const message =
        error instanceof Error
          ? error.message
          : "The photo could not be checked. Retry.";
      setError(
        error instanceof ApiError && error.code === "SAMPLE_LOW_QUALITY"
          ? message
              .split(", ")
              .map((reason) => QUALITY_MESSAGES[reason] ?? reason)
              .join(" ")
          : message,
      );
    } finally {
      captureLock.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  async function save() {
    if (saving || samples.length !== 3) return;
    setSaving(true);
    setError("");
    const result = await addMember(id, name, samples);
    if (!mounted.current) return;
    setSaving(false);
    if (result.ok) onClose();
    else setError(result.message);
  }
  return (
    <Modal
      wide
      title="A new familiar face"
      description="Create your attendance profile in three simple steps."
      onClose={() => {
        if (!saving) onClose();
      }}
    >
      <div className="registration-progress">
        <span className="current">
          <i>{step > 0 ? <Check size={12} /> : "1"}</i>Profile
        </span>
        <b />
        <span className={step >= 1 ? "current" : ""}>
          <i>2</i>Face samples
        </span>
        <b />
        <span className={step === 2 ? "current" : ""}>
          <i>3</i>Review
        </span>
      </div>
      {step === 0 && (
        <form onSubmit={continueToCapture} className="registration-form">
          <div className="registration-symbol">
            <CircleUserRound size={38} strokeWidth={1} />
          </div>
          <label htmlFor="member-name">Full name</label>
          <input
            id="member-name"
            autoFocus
            autoComplete="name"
            maxLength={120}
            placeholder="Your full name"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setError("");
            }}
            required
          />
          <label htmlFor="member-id">
            Member ID <span>or student number</span>
          </label>
          <input
            id="member-id"
            maxLength={64}
            placeholder="Your student number or unique ID"
            value={id}
            onChange={(event) => {
              setId(event.target.value);
              setError("");
            }}
            required
          />
          <p className="field-hint">
            Use your own unique ID. Your name, ID and face embeddings will be
            saved for future attendance.
          </p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="modal-actions">
            <button type="button" className="text-button" onClick={onClose}>
              Cancel
            </button>
            <button
              className="capsule primary-capsule"
              type="submit"
              disabled={!ready}
            >
              Continue <ChevronRight size={15} />
            </button>
          </div>
        </form>
      )}
      {step === 1 && (
        <div className="capture-step">
          <div className="capture-heading">
            <p>
              {samples.length < 3
                ? angles[samples.length]
                : "All three angles, collected."}
            </p>
            <span className="field-hint">
              {samples.length}/3 verified photos
            </span>
          </div>
          <div className="registration-camera">
            <video
              ref={camera.videoRef}
              autoPlay
              muted
              playsInline
              className={preferences.mirrorCamera ? "mirrored" : ""}
            />
            {!camera.stream && (
              <div className="camera-placeholder">
                <Camera size={28} strokeWidth={1} />
                <p>
                  {camera.loading
                    ? "Opening your camera…"
                    : camera.error ||
                      "Allow camera access, then keep one face in view."}
                </p>
                {camera.error ? (
                  <button className="capsule" onClick={camera.retry}>
                    Retry camera
                  </button>
                ) : (
                  !cameraOn && (
                    <button
                      className="capsule"
                      onClick={() => setCameraOn(true)}
                    >
                      Turn on camera
                    </button>
                  )
                )}
              </div>
            )}
            <div className="registration-face-guide" />
          </div>
          <div className="sample-slots">
            {angles.map((angle, index) => (
              <div
                key={angle}
                className={
                  samples[index] ? "sample-slot captured" : "sample-slot"
                }
              >
                {samples[index] ? (
                  <img
                    src={samples[index]}
                    alt={name + ", " + angle.toLowerCase()}
                  />
                ) : (
                  <Camera size={19} />
                )}
                <span>{["Front", "Left", "Right"][index]}</span>
                {samples[index] && <Check size={12} />}
              </div>
            ))}
          </div>
          <p className="field-hint">
            Stand about 40–70 cm away in even lighting. Turn only slightly for
            the side views. Each photo is checked before it is accepted.
          </p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="modal-actions">
            <button
              className="text-button"
              disabled={busy}
              onClick={() => {
                setCameraOn(false);
                setStep(0);
              }}
            >
              <ChevronLeft size={14} /> Back
            </button>
            <div>
              {samples.length > 0 && (
                <button
                  className="icon-button"
                  aria-label="Retake samples"
                  disabled={busy}
                  onClick={() => {
                    setSamples([]);
                    setError("");
                  }}
                >
                  <RotateCcw size={16} />
                </button>
              )}
              {samples.length < 3 ? (
                <button
                  className="capsule primary-capsule"
                  onClick={capture}
                  disabled={!camera.stream || busy}
                >
                  {busy ? (
                    <LoaderCircle size={15} className="spin" />
                  ) : (
                    <Camera size={15} />
                  )}
                  {busy
                    ? "Checking photo…"
                    : "Capture sample " + (samples.length + 1)}
                </button>
              ) : (
                <button
                  className="capsule primary-capsule"
                  onClick={() => {
                    setCameraOn(false);
                    setStep(2);
                  }}
                >
                  Review profile <ChevronRight size={15} />
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      {step === 2 && (
        <div className="review-step">
          <div className="review-orb">
            <Check size={29} strokeWidth={1.3} />
          </div>
          <h3>Nice to meet you, {name.split(" ")[0]}.</h3>
          <p>Your face samples are ready to enroll.</p>
          <dl className="review-details">
            <div>
              <dt>Full name</dt>
              <dd>{name.trim()}</dd>
            </div>
            <div>
              <dt>Member ID</dt>
              <dd>{id.trim()}</dd>
            </div>
            <div>
              <dt>Verified photos</dt>
              <dd>
                3 of 3 <Check size={13} />
              </dd>
            </div>
          </dl>
          <p className="field-hint">
            Save to create your attendance profile. Your identity and face
            embeddings are stored in the backend database. You can then check in
            from Attendance.
          </p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="modal-actions">
            <button
              className="text-button"
              disabled={saving}
              onClick={() => {
                setError("");
                setStep(1);
              }}
            >
              <ChevronLeft size={14} /> Back
            </button>
            <button
              className="capsule primary-capsule"
              onClick={save}
              disabled={saving || !ready}
            >
              {saving ? (
                <LoaderCircle size={15} className="spin" />
              ) : (
                <Check size={15} />
              )}
              {saving ? "Saving profile…" : "Save profile"}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
