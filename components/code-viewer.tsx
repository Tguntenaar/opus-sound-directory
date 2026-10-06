"use client";

import { useEffect, useState } from "react";
import { CopyButton } from "@/components/copy-button";

export function CodeViewer({
  assetPath,
  entryId,
}: {
  assetPath: string;
  entryId: string;
}) {
  const [code, setCode] = useState<string>("Loading…");

  useEffect(() => {
    let cancelled = false;
    fetch(assetPath)
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error("not found"))))
      .then((text) => {
        if (!cancelled) setCode(text);
      })
      .catch(() => {
        if (!cancelled) setCode("# Unable to load generate.py");
      });
    return () => {
      cancelled = true;
    };
  }, [assetPath]);

  const canCopy = code.length > 0 && !code.startsWith("Loading") && !code.startsWith("# Unable");

  return (
    <div className="flex flex-col gap-2">
      {canCopy && (
        <div className="flex justify-end">
          <CopyButton text={code} entryId={entryId} label="Copy code" />
        </div>
      )}
      <pre
        className="max-h-[28rem] overflow-auto rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-xs leading-relaxed text-zinc-300 transition-colors hover:border-zinc-700/90"
        tabIndex={0}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}
