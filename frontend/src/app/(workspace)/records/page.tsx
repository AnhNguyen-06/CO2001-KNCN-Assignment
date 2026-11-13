import type { Metadata } from "next";
import { Suspense } from "react";
import { Records } from "@/components/records";

export const metadata: Metadata = { title: "Records" };
export default function RecordsPage() {
  return (
    <Suspense
      fallback={<div className="page-loading">Loading your records…</div>}
    >
      <Records />
    </Suspense>
  );
}
