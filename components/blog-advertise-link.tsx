"use client";

import Link from "next/link";
import { captureEvent } from "@/lib/analytics-client";

export function BlogAdvertiseLink() {
  return (
    <Link
      href="/sponsor?ref=blog"
      className="text-zinc-600 underline-offset-2 transition-colors hover:text-zinc-400 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
      onClick={() =>
        captureEvent("sponsor_cta_click", {
          placement: "blog-index",
          slug: "",
          sponsored: false,
        })
      }
    >
      Advertise here
    </Link>
  );
}
