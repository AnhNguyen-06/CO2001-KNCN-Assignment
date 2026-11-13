"use client";

import { useEffect, useRef, useState } from "react";

export function useCamera(enabled: boolean) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let ownedStream: MediaStream | null = null;
    setError("");
    setStream(null);
    if (!enabled) {
      setLoading(false);
      return;
    }
    setLoading(true);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError(
        "Camera access requires HTTPS or localhost in a supported browser.",
      );
      setLoading(false);
      return;
    }
    navigator.mediaDevices
      .getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user",
        },
        audio: false,
      })
      .then((result) => {
        if (cancelled) {
          result.getTracks().forEach((track) => track.stop());
          return;
        }
        ownedStream = result;
        setStream(result);
        setLoading(false);
        result.getVideoTracks().forEach((track) =>
          track.addEventListener("ended", () => {
            if (!cancelled) {
              setStream(null);
              setError("The camera disconnected. Reconnect it and try again.");
            }
          }),
        );
      })
      .catch((reason: DOMException) => {
        if (cancelled) return;
        setLoading(false);
        setError(
          reason.name === "NotAllowedError"
            ? "Camera permission was denied. Allow access in your browser, then retry."
            : reason.name === "NotFoundError"
              ? "No camera was found. Connect a webcam and retry."
              : "The camera could not start. Close other camera apps and retry.",
        );
      });
    return () => {
      cancelled = true;
      ownedStream?.getTracks().forEach((track) => track.stop());
    };
  }, [enabled, attempt]);

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = stream;
  }, [stream]);

  function capture(maxWidth = 960): string | null {
    const video = videoRef.current;
    if (!video || video.readyState < 2 || !video.videoWidth) return null;
    const canvas = document.createElement("canvas");
    canvas.width = Math.min(maxWidth, video.videoWidth);
    canvas.height = Math.round(
      (canvas.width * video.videoHeight) / video.videoWidth,
    );
    canvas
      .getContext("2d")
      ?.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.75);
  }

  return {
    videoRef,
    stream,
    error,
    loading,
    capture,
    retry: () => setAttempt((value) => value + 1),
  };
}
