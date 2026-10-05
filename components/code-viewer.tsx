"use client";

import { useEffect, useState } from "react";

export function CodeViewer({ assetPath }: { assetPath: string }) {
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

  return (
    <pre
      className="max-h-[28rem] overflow-auto rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-xs leading-relaxed text-zinc-300"
      tabIndex={0}
    >
      <code>{code}</code>
    </pre>
  );
}
