export type Member = {
  id: string;
  name: string;
  role: string;
  color: string;
  joinedAt: string;
  samples: number;
};
export type AttendanceRecord = {
  id: string;
  memberId: string;
  name: string;
  recordedAt: string;
  date: string;
  source: "camera";
};
export type ExportState = {
  attendance_date: string;
  data_revision: number;
  exported_revision: number;
  status: "synced" | "pending" | "error";
  last_error: string | null;
};
export type Preferences = {
  mirrorCamera: boolean;
  showGuide: boolean;
  reduceMotion: boolean;
};
export const DEFAULT_PREFERENCES: Preferences = {
  mirrorCamera: true,
  showGuide: true,
  reduceMotion: false,
};
export function localDate(date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}
export function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Ho_Chi_Minh",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}
export function displayDate(value: string, short = false) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Ho_Chi_Minh",
    day: "numeric",
    month: short ? "short" : "long",
    year: "numeric",
  }).format(new Date(value + "T12:00:00+07:00"));
}
export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}
