/** Human-readable model / generation attribution (never imply Opus when synth was local). */

export const LOCAL_SYNTH_MODEL_ID = "local-synth";

/** Default Anthropic Opus model id for future `--agent` runs (Messages API). */
export const TARGET_OPUS_MODEL_ID = "claude-opus-4-20250514";

const DISPLAY: Record<string, { label: string; detail?: string }> = {
  [LOCAL_SYNTH_MODEL_ID]: {
    label: "Local numpy synth",
    detail: "Runner verification pipeline (not an API model call)",
  },
  "claude-opus-4-20250514": {
    label: "Claude Opus 4",
    detail: "Anthropic Messages API",
  },
  "claude-opus-4-5": {
    label: "Claude Opus 4.5",
    detail: "Anthropic Messages API",
  },
  "claude-opus-5-5": {
    label: "Claude Opus 5.5 (display id)",
    detail: "Legacy placeholder — use local-synth or a real API id",
  },
};

export function modelAttribution(modelId: string, targetModelId?: string): {
  primary: string;
  secondary?: string;
  isLocalSynth: boolean;
} {
  const isLocal = modelId === LOCAL_SYNTH_MODEL_ID;
  const known = DISPLAY[modelId];
  const primary = isLocal
    ? `Made with ${DISPLAY[LOCAL_SYNTH_MODEL_ID].label}`
    : known
      ? `Made with ${known.label}`
      : `Made with ${modelId}`;
  let secondary: string | undefined;
  if (isLocal && targetModelId) {
    const target = DISPLAY[targetModelId];
    secondary = target
      ? `Agent target: ${target.label} (\`${targetModelId}\`)`
      : `Agent target: \`${targetModelId}\``;
  } else if (known?.detail) {
    secondary = known.detail;
  }
  return { primary, secondary, isLocalSynth: isLocal };
}
