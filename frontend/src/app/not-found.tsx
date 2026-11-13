import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { BrandMark } from "@/components/instruments";

export default function NotFound() {
  return (
    <main className="not-found">
      <BrandMark />
      <p className="ruled-eyebrow">A quiet corner of the internet</p>
      <h1 className="luminous">Nothing here just yet.</h1>
      <p>Let’s get you back to familiar faces.</p>
      <Link className="capsule" href="/attendance">
        <ArrowLeft size={14} /> Back to the workspace
      </Link>
    </main>
  );
}
