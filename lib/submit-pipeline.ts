import { audioExtension, validateAudioUrlSize } from "@/lib/audio-url-policy";
import { saveCommunityEntry } from "@/lib/community-kv";
import { COMMUNITY_MODEL_ID } from "@/lib/community-types";
import type { CommunitySoundEntry } from "@/lib/community-types";
import { SUBMIT_LICENSE_NOTE } from "@/lib/licenses";
import { getSiteUrl } from "@/lib/site-url";
import { runAiReview } from "@/lib/submit-ai-review";
import { staticScreenSubmission, resolveCode } from "@/lib/submit-screen";
import { getSubmitEntry, updateSubmitEntry } from "@/lib/submit-kv";
import { notifySubmitEntry } from "@/lib/submit-notify";
import type { SubmitEntry } from "@/lib/submit-types";
import { scheduleBackground } from "@/lib/schedule-background";
import { captureServerEvent } from "@/lib/posthog-server";

function slugifyTitle(title: string, id: string): string {
  const base = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
  const suffix = id.replace(/-/g, "").slice(0, 8);
  return `${base || "community"}-${suffix}`;
}

async function buildCommunityEntry(
  submission: SubmitEntry,
  slug: string,
  hasRenderedAudio: boolean,
  audioUrl?: string,
): Promise<{ entry: CommunitySoundEntry; code: string }> {
  const code = resolveCode(submission) ?? "# generate.py missing";
  const durationSec = submission.durationSec ?? 15;
  const fps = 30;
  const sampleRate = 48000;
  const samples = Math.round(durationSec * sampleRate);

  let mp3 = "";
  let wav = "";
  if (hasRenderedAudio && audioUrl) {
    const ext = audioExtension(audioUrl);
    if (ext === "mp3") mp3 = audioUrl;
    if (ext === "wav") wav = audioUrl;
    if (ext === "mp3" && !wav) wav = audioUrl;
    if (ext === "wav" && !mp3) mp3 = audioUrl;
  }

  const entry: CommunitySoundEntry = {
    id: slug,
    slug,
    title: submission.title,
    category: submission.category,
    tags: ["community"],
    mood: submission.mood,
    tempo: submission.tempo,
    prompt: submission.prompt,
    modelId: COMMUNITY_MODEL_ID,
    generatedAt: new Date().toISOString().slice(0, 10),
    seed: 0,
    timing: {
      bpm: 120,
      fps,
      durationSec,
      samples,
      sampleRate,
    },
    cues: [{ frame: 0, label: "start" }],
    master: { targetLufs: -14, truePeakDbTp: -1 },
    metrics: {
      lufs: null,
      truePeak: null,
      durationSec,
      passedChecks: false,
    },
    assets: {
      wav,
      mp3,
      spectrogram: "",
      code: `/api/community/${slug}/code`,
    },
    notes: [
      submission.notes,
      "Community submission — prompt and code published after automated review. Audio may be external or not yet rendered.",
      SUBMIT_LICENSE_NOTE,
    ]
      .filter(Boolean)
      .join("\n\n"),
    isCommunity: true,
    submissionId: submission.id,
    author: submission.author_name
      ? {
          name: submission.author_name,
          url: submission.author_url,
        }
      : undefined,
    hasRenderedAudio,
    codeApiPath: `/api/community/${slug}/code`,
  };

  return { entry, code };
}

export async function publishSubmissionAsCommunity(
  submissionId: string,
): Promise<string | null> {
  const submission = await getSubmitEntry(submissionId);
  if (!submission) return null;
  let hasRenderedAudio = false;
  let audioUrl = submission.audioUrl;
  if (audioUrl) {
    hasRenderedAudio = await validateAudioUrlSize(audioUrl);
    if (!hasRenderedAudio) audioUrl = undefined;
  }
  const slug = slugifyTitle(submission.title, submission.id);
  const { entry, code } = await buildCommunityEntry(
    submission,
    slug,
    hasRenderedAudio,
    audioUrl,
  );
  await saveCommunityEntry(entry, code);
  await updateSubmitEntry(submissionId, {
    status: "live",
    communitySlug: slug,
  });
  scheduleBackground(
    captureServerEvent({
      distinctId: `submission:${submissionId}`,
      event: "submit_status_live",
      properties: {
        submission_id: submissionId,
        community_slug: slug,
        source: submission.source,
      },
    }),
  );
  return slug;
}

export async function runSubmissionPipeline(submissionId: string): Promise<void> {
  const submission = await getSubmitEntry(submissionId);
  if (!submission || submission.status !== "scanning") return;

  const screen = staticScreenSubmission(submission);
  await updateSubmitEntry(submissionId, { screening: screen.flags });

  if (!screen.ok) {
    await updateSubmitEntry(submissionId, {
      status: "rejected",
      reviewerNote: screen.reason,
    });
    return;
  }

  const aiReview = await runAiReview(submission);
  await updateSubmitEntry(submissionId, { aiReview });

  if (aiReview.verdict === "malicious") {
    await updateSubmitEntry(submissionId, {
      status: "rejected",
      reviewerNote: aiReview.reasons.join("; ") || "Malicious content",
    });
    return;
  }

  const autoApprove =
    aiReview.verdict === "safe" && aiReview.quality >= 3 && aiReview.categoryFit;

  if (!autoApprove) {
    await updateSubmitEntry(submissionId, { status: "pending_review" });
    const latest = await getSubmitEntry(submissionId);
    if (latest) await notifySubmitEntry(latest);
    return;
  }

  let hasRenderedAudio = false;
  let audioUrl = submission.audioUrl;
  if (audioUrl) {
    hasRenderedAudio = await validateAudioUrlSize(audioUrl);
    if (!hasRenderedAudio) audioUrl = undefined;
  }

  const slug = slugifyTitle(submission.title, submission.id);
  const { entry, code } = await buildCommunityEntry(
    submission,
    slug,
    hasRenderedAudio,
    audioUrl,
  );
  await saveCommunityEntry(entry, code);

  await updateSubmitEntry(submissionId, {
    status: "live",
    communitySlug: slug,
  });

  scheduleBackground(
    captureServerEvent({
      distinctId: `submission:${submissionId}`,
      event: "submit_status_live",
      properties: {
        submission_id: submissionId,
        community_slug: slug,
        source: submission.source,
      },
    }),
  );

  const latest = await getSubmitEntry(submissionId);
  if (latest) await notifySubmitEntry(latest);
}

export function submissionReviewUrl(submission: SubmitEntry): string | undefined {
  if (submission.status === "live" && submission.communitySlug) {
    return `${getSiteUrl()}/e/${submission.communitySlug}`;
  }
  return undefined;
}
