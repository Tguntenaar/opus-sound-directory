export async function GET() {
  try {
    const response = await fetch("https://api.github.com/repos/Tguntenaar/opus-sound-directory", {
      headers: { Accept: "application/vnd.github+json", "User-Agent": "Opus-Sounds-Directory" },
      signal: AbortSignal.timeout(5000),
      cf: { cacheTtl: 3600, cacheEverything: true },
    });
    if (!response.ok) throw new Error("GitHub unavailable");
    const data = await response.json() as { stargazers_count?: number };
    if (!Number.isSafeInteger(data.stargazers_count) || data.stargazers_count! < 0) throw new Error("Invalid count");
    return Response.json({ stars: data.stargazers_count }, {
      headers: { "Cache-Control": "public, max-age=300, s-maxage=3600" },
    });
  } catch {
    return Response.json({ stars: null }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
