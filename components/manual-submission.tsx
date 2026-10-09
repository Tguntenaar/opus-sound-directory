"use client";

import { useState } from "react";
import { SubmitEntryForm } from "@/components/submit-entry-form";
import { captureEvent } from "@/lib/analytics-client";

export function ManualSubmission() {
  const [opened, setOpened] = useState(false);
  return (
    <details className="rounded-xl border border-zinc-800 p-5 sm:p-6" onToggle={(event) => {
      if (event.currentTarget.open && !opened) {
        setOpened(true);
        captureEvent("submit_manual_open", { source: "submit_page" });
      }
    }}>
      <summary className="cursor-pointer text-sm font-medium text-zinc-200 focus-visible:outline-violet-400">Or submit manually</summary>
      <div className="mt-6">{opened && <SubmitEntryForm />}</div>
    </details>
  );
}
