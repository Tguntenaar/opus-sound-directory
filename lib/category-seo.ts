import { CATEGORY_ORDER } from "@/lib/categories";

export type CategoryFaq = { q: string; a: string };

export type CategorySeoContent = {
  h1: string;
  intro: string;
  faq: CategoryFaq[];
};

export const CATEGORY_SEO: Record<string, CategorySeoContent> = {
  "ad-beds": {
    h1: "Free Royalty-Free Ad Music Beds by Length",
    intro:
      "Download CC0 ad beds at 6, 15, 30, and 60 seconds — synthesised for TikTok, Reels, and Shorts, with WAV, MP3, prompts, and LUFS metrics.",
    faq: [
      {
        q: "Can I use these ad beds in paid social ads?",
        a: "Yes. Sounds are CC0 (public domain). You can use them in commercial ads without attribution.",
      },
      {
        q: "Why are beds listed by exact seconds?",
        a: "Each bed is synthesised to a fixed sample count so cuts land on frame boundaries at 30 fps.",
      },
      {
        q: "What loudness should a 15 second ad bed target?",
        a: "Most entries target about −14 LUFS integrated with true peak at or below −1 dBTP, measured with ffmpeg ebur128.",
      },
    ],
  },
  "ui-sounds": {
    h1: "Free UI & App Sound Effects",
    intro:
      "Short success, error, and notification sounds for product demos and AI-generated app videos — preview, download WAV/MP3, copy the synthesis prompt.",
    faq: [
      {
        q: "How long should a UI success sound be?",
        a: "Usually under one second. Entries here range from a few hundred milliseconds to about half a second.",
      },
      {
        q: "Are these realistic instrument recordings?",
        a: "No. They are synthesised in Python (numpy/scipy) from written prompts, not sample libraries.",
      },
      {
        q: "Can I match these to my brand palette?",
        a: "Copy the prompt and code, change seed or timbre targets, and re-run the runner to iterate.",
      },
    ],
  },
  "logo-stings": {
    h1: "Free Logo Sting Sound Effects",
    intro:
      "Bright, short logo moments for intros and outros — royalty-free stings with spectrograms, code, and loudness numbers.",
    faq: [
      {
        q: "What is a logo sting?",
        a: "A brief sound (often 2–4 seconds) that plays when a logo appears on screen.",
      },
      {
        q: "Do logo stings loop?",
        a: "These are one-shot stings with a defined ending, not seamless loops.",
      },
      {
        q: "What format are downloads?",
        a: "48 kHz stereo WAV and MP3 previews, with the Python that generated each file.",
      },
    ],
  },
  drops: {
    h1: "Free Whoosh & Transition Sound Effects",
    intro:
      "Impacts, whooshes, and cut helpers for edits — grab a free whoosh sound effect or heavy drop for video transitions.",
    faq: [
      {
        q: "What is a whoosh stinger used for?",
        a: "To sell a fast camera move, scene change, or title reveal — usually synced to a single frame.",
      },
      {
        q: "Are these one-shots or loops?",
        a: "One-shots with a clear peak; duration is listed per entry.",
      },
      {
        q: "Can I layer these under music?",
        a: "Yes. Check integrated LUFS on the page and gain-stage in your editor.",
      },
    ],
  },
  risers: {
    h1: "Free Riser Sound Effects for Video",
    intro:
      "Tension builds that land on a frame — riser sound effects for TikTok hooks, trailers, and reveal moments, with timed cues in each prompt.",
    faq: [
      {
        q: "What is a riser in video editing?",
        a: "A rising sound (noise, pitch, or energy) that peaks when something important happens on screen.",
      },
      {
        q: "How do I sync a riser to a cut?",
        a: "Use the cue frames in each entry’s prompt, or align the spectrogram peak to your timeline playhead.",
      },
      {
        q: "Are risers royalty-free?",
        a: "Yes — CC0 synthesised audio with no attribution required.",
      },
    ],
  },
  "chaos-calm": {
    h1: "Free Chaos-to-Calm Transition Beds",
    intro:
      "Beds that move from noisy tension into a calm pad — timed for short-form story arcs and before/after edits.",
    faq: [
      {
        q: "What does chaos → calm mean?",
        a: "The prompt specifies cue frames where busy textures stop and a warmer bed takes over.",
      },
      {
        q: "Can I use these for TikTok story ads?",
        a: "Yes. Several beds are 8–30 seconds with BPM and frame cues for vertical video.",
      },
      {
        q: "How were these made?",
        a: "Synthesised in Python from numeric prompts; see model attribution on each entry.",
      },
    ],
  },
  ambient: {
    h1: "Free Ambient Music Beds for Video",
    intro:
      "Background pads and lo-fi textures for underscoring talking head or B-roll — low-distraction beds with length and LUFS listed.",
    faq: [
      {
        q: "Are ambient beds loopable?",
        a: "They are rendered to a fixed length with a fade-out, not seamless loops.",
      },
      {
        q: "What loudness are ambient beds?",
        a: "Integrated LUFS is measured per file; use the metrics panel on each entry.",
      },
      {
        q: "Can I extend a bed?",
        a: "Copy the prompt and code and ask an LLM or runner to render a longer duration with the same seed approach.",
      },
    ],
  },
  meme: {
    h1: "Free Meme & Reaction Sound Effects",
    intro:
      "Original shock booms, wah-wah fails and comedic stings for reaction cuts and memes — synthesised from scratch in Python, never sampled from a viral clip.",
    faq: [
      {
        q: "Are these the original meme sounds?",
        a: "No. Each one is an original synthesis written as code, built to feel familiar without copying any existing recording.",
      },
      {
        q: "Can I use them in YouTube, TikTok or Reels videos?",
        a: "Yes. Sounds are CC0 (public domain), so you can use them commercially without attribution.",
      },
      {
        q: "How do I make my own variation?",
        a: "Copy the prompt and code on any entry and ask Claude to change the pitch, length or texture.",
      },
    ],
  },
  gaming: {
    h1: "Free Retro Game & Arcade Sound Effects",
    intro:
      "Original chiptune jingles and arcade effects built from band-limited oscillators on a 60 Hz frame clock — no game's melody copied, all royalty-free.",
    faq: [
      {
        q: "Are these copied from classic games?",
        a: "No. Every contour is original; the code only borrows the style of early sound chips.",
      },
      {
        q: "Will they alias like cheap chiptune plugins?",
        a: "No. Oscillators are band-limited (additive), so there are no aliasing artefacts.",
      },
      {
        q: "Can I use them in my game?",
        a: "Yes. They are CC0: commercial use, no attribution needed.",
      },
    ],
  },
  cinematic: {
    h1: "Free Cinematic Braams & Trailer Hits",
    intro:
      "Trailer-style braams and heavy impacts with sub, crack and dark hall tails — frame-locked hits you can drop on a cut.",
    faq: [
      {
        q: "Does the braam copy any famous sound mark?",
        a: "No. It is a hard original hit — no converging glissando and no resolution modelled on a registered sound mark.",
      },
      {
        q: "Where does the hit land?",
        a: "Each entry lists the cue frame at 30 fps; the hit lands within 5 ms of it.",
      },
      {
        q: "Are they royalty-free?",
        a: "Yes — CC0 synthesised audio with no attribution required.",
      },
    ],
  },
  "retro-tech": {
    h1: "Free Retro Tech Sounds: Dial-Up Modem & More",
    intro:
      "Nostalgic machine sounds rebuilt from the protocols up — dial tones, DTMF and a full 56k modem handshake, all synthesised in code.",
    faq: [
      {
        q: "Is the modem sound a recording?",
        a: "No. It is synthesised from the real signalling: dial tone, DTMF, answer tone with phase reversals, FSK, line probing and training.",
      },
      {
        q: "Can I use it commercially?",
        a: "Yes. Sounds are CC0 (public domain).",
      },
      {
        q: "Why does it sound like a phone line?",
        a: "Everything is band-limited to a 300–3,400 Hz telephone line with line hiss, as the original was.",
      },
    ],
  },
  guitar: {
    h1: "Free Guitar Licks, Loops & Stings",
    intro:
      "Expressive guitar sounds built entirely in code — clean neo-soul licks, singing blues bends, fingerstyle acoustic loops and funk rhythm grooves, every string modelled from scratch.",
    faq: [
      {
        q: "Are these guitar recordings or samples?",
        a: "No. Every note is a physically modelled string (waveguide or additive synthesis) with pick, body, pickup, amp and cabinet models written in Python.",
      },
      {
        q: "Do they copy any famous riff or player?",
        a: "No. Every phrase is an original composition; only general genre idioms such as pentatonic licks and travis picking are used.",
      },
      {
        q: "Can I use them commercially?",
        a: "Yes. Sounds are CC0 (public domain), so you can use them without attribution.",
      },
    ],
  },
};

export function isValidCategorySlug(slug: string): boolean {
  return (CATEGORY_ORDER as readonly string[]).includes(slug);
}

export function getCategorySeo(slug: string): CategorySeoContent | undefined {
  return CATEGORY_SEO[slug];
}
