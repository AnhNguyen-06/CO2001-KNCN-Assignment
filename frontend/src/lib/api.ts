export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(28000),
    ...options,
  });
  const payload = await response.json().catch(() => {
    throw new ApiError(
      "BACKEND_UNAVAILABLE",
      "The recognition service is starting or temporarily unavailable. Please retry shortly.",
    );
  });
  if (!response.ok) {
    const detail = payload.detail ?? payload;
    throw new ApiError(
      detail.code ?? "REQUEST_FAILED",
      detail.message ?? "The request could not be completed. Please retry.",
    );
  }
  return payload as T;
}

export function post<T>(path: string, payload?: unknown, signal?: AbortSignal) {
  return api<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload === undefined ? undefined : JSON.stringify(payload),
    signal,
  });
}

export type RecognitionFace = {
  bbox: [number, number, number, number];
  landmarks: number[][];
  name: string | null;
  quality: {
    accepted: boolean;
    reasons: string[];
    metrics: Record<string, number>;
  };
  match: { decision: string; person_id: string | null; score: number | null };
  state: string;
  track_id: number;
};

export type RecognitionResult = {
  faces: RecognitionFace[];
  events: { kind: string; message: string; data: Record<string, unknown> }[];
  processing_ms: number;
  image_width: number;
  image_height: number;
  stale: boolean;
};

export const QUALITY_MESSAGES: Record<string, string> = {
  face_too_small: "Move closer to the camera.",
  eyes_too_close: "Move closer and face the camera.",
  face_clipped: "Keep your entire face inside the camera view.",
  face_tilted: "Keep your head upright.",
  face_turned_too_far: "Turn back slightly toward the camera.",
  too_dark: "Move toward better lighting.",
  too_bright: "Reduce direct light on your face.",
  too_blurry: "Hold still for a sharper photo.",
};

export async function downloadRecords(
  filters: { date?: string; memberId?: string; query?: string } = {},
) {
  const params = new URLSearchParams();
  if (filters.date) params.set("date", filters.date);
  if (filters.memberId) params.set("member_id", filters.memberId);
  if (filters.query) params.set("q", filters.query);
  const response = await fetch(`/api/exports/download?${params}`, {
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error("The Excel download could not be prepared. Please retry.");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = `attendance_${filters.date?.replaceAll("-", "_") ?? "records"}.xlsx`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
