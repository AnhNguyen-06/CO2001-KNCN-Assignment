"use client";

import { RefObject, useEffect, useRef, useState } from "react";
import { api, post, RecognitionResult } from "./api";

export function useRecognition(
  enabled: boolean,
  videoRef: RefObject<HTMLVideoElement | null>,
  capture: () => string | null,
  onResult: (value: RecognitionResult) => void,
) {
  const [result, setResult] = useState<RecognitionResult | null>(null);
  const [error, setError] = useState("");
  const [connecting, setConnecting] = useState(false);
  const captureRef = useRef(capture);
  captureRef.current = capture;
  const onResultRef = useRef(onResult);
  onResultRef.current = onResult;
  useEffect(() => {
    if (!enabled) {
      setConnecting(false);
      setResult(null);
      return;
    }
    let stopped = false;
    let token: string | null = null;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController | null = null;
    let frameId = 0;
    setError("");
    setConnecting(true);
    setResult(null);
    const close = () => {
      if (token)
        void fetch(`/api/recognition/sessions/${token}`, {
          method: "DELETE",
          keepalive: true,
        }).catch(() => {});
    };
    const unload = () => {
      stopped = true;
      controller?.abort();
      close();
    };
    window.addEventListener("pagehide", unload);
    async function nextFrame() {
      if (stopped || !token) return;
      const started = performance.now();
      const photo =
        videoRef.current?.readyState && videoRef.current.readyState >= 2
          ? captureRef.current()
          : null;
      if (!photo) {
        timer = setTimeout(nextFrame, 150);
        return;
      }
      controller = new AbortController();
      try {
        const binary = atob(photo.split(",")[1]);
        const bytes = Uint8Array.from(binary, (character) =>
          character.charCodeAt(0),
        );
        const value = await api<RecognitionResult>(
          `/recognition/sessions/${token}/frames?frame_id=${++frameId}`,
          {
            method: "POST",
            headers: { "Content-Type": "image/jpeg" },
            body: new Blob([bytes], { type: "image/jpeg" }),
            signal: controller.signal,
          },
        );
        if (stopped) return;
        setResult(value);
        setConnecting(false);
        onResultRef.current(value);
        timer = setTimeout(
          nextFrame,
          Math.max(0, 200 - (performance.now() - started)),
        );
      } catch (error) {
        if (!stopped && !controller.signal.aborted) {
          setError(
            error instanceof Error
              ? error.message
              : "Recognition disconnected. Turn the camera on again.",
          );
          setConnecting(false);
          close();
        }
      }
    }
    post<{ token: string }>("/recognition/sessions")
      .then((lease) => {
        token = lease.token;
        if (stopped) close();
        else void nextFrame();
      })
      .catch((error) => {
        if (!stopped) {
          setError(error.message);
          setConnecting(false);
        }
      });
    return () => {
      stopped = true;
      clearTimeout(timer);
      controller?.abort();
      close();
      window.removeEventListener("pagehide", unload);
    };
  }, [enabled, videoRef]);
  return { result, error, connecting };
}
