/** Human-readable model / generation attribution (never imply Opus when synth was local). */

export const LOCAL_SYNTH_MODEL_ID = "local-synth";

/** Default Anthropic Opus model id for future `--agent` runs (Messages API). */
export const TARGET_OPUS_MODEL_ID = "claude-opus-5-5";

export const COMMUNITY_MODEL_ID = "community";

const DISPLAY: Record<string, { label: string; detail?: string }> = {
  [COMMUNITY_MODEL_ID]: {
    label: "Community submission",
    detail: "Published via automated review — not Opus-generated unless proven",
  },
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
    label: "Claude Opus 5.5",
    detail: "Anthropic Messages API",
  },
};

export function isOpusApiModelId(modelId: string): boolean {
  return modelId !== LOCAL_SYNTH_MODEL_ID && modelId.startsWith("claude-opus");
}

export function modelAttribution(modelId: string, targetModelId?: string): {
  primary: string;
  secondary?: string;
  isLocalSynth: boolean;
} {
  const isLocal = modelId === LOCAL_SYNTH_MODEL_ID;
  const isCommunity = modelId === COMMUNITY_MODEL_ID;
  const known = DISPLAY[modelId];
  const primary = isCommunity
    ? DISPLAY[COMMUNITY_MODEL_ID].label
    : isLocal
      ? `Made with ${DISPLAY[LOCAL_SYNTH_MODEL_ID].label}`
      : known
        ? `Made with ${known.label}`
        : `Made with ${modelId}`;
  let secondary: string | undefined;
  if (isOpusApiModelId(modelId)) {
    secondary = known?.detail;
  } else if (known?.detail && !isLocal && !isCommunity) {
    secondary = known.detail;
  } else if (isCommunity) {
    secondary = DISPLAY[COMMUNITY_MODEL_ID].detail;
  }
  return { primary, secondary, isLocalSynth: isLocal };
}
