import type { Metadata } from "next";
import { Attendance } from "@/components/attendance";

export const metadata: Metadata = { title: "Attendance" };
export default function AttendancePage() {
  return <Attendance />;
}
