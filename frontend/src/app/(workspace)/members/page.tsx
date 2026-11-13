import type { Metadata } from "next";
import { Suspense } from "react";
import { Members } from "@/components/members";

export const metadata: Metadata = { title: "Members" };
export default function MembersPage() {
  return (
    <Suspense
      fallback={<div className="page-loading">Loading your people…</div>}
    >
      <Members />
    </Suspense>
  );
}
