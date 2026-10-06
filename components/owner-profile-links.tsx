import { IconTooltip } from "@/components/icon-tooltip";
import { GithubIcon, XLogoIcon } from "@/components/social-icons";
import { OWNER_GITHUB_PROFILE, OWNER_X_PROFILE } from "@/lib/owner-profiles";
import { cn } from "@/lib/utils";

const linkClass =
  "inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-900/80 hover:text-zinc-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60";

type Props = {
  className?: string;
  /** Footer uses slightly muted hover bg. */
  variant?: "default" | "footer";
};

export function OwnerProfileLinks({ className, variant = "default" }: Props) {
  const cls =
    variant === "footer"
      ? cn(
          linkClass,
          "hover:bg-zinc-900/60 hover:text-zinc-400",
          className,
        )
      : cn(linkClass, className);

  return (
    <>
      <IconTooltip label="GitHub · @Tguntenaar">
        <a
          href={OWNER_GITHUB_PROFILE}
          className={cls}
          target="_blank"
          rel="me noopener noreferrer"
          aria-label="GitHub · @Tguntenaar"
        >
          <GithubIcon />
        </a>
      </IconTooltip>
      <IconTooltip label="X · @Tguntenaar">
        <a
          href={OWNER_X_PROFILE}
          className={cls}
          target="_blank"
          rel="me noopener noreferrer"
          aria-label="X · @Tguntenaar"
        >
          <XLogoIcon />
        </a>
      </IconTooltip>
    </>
  );
}
