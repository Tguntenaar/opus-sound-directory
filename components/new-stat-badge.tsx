import { cn } from "@/lib/utils";

export function NewStatBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center rounded-md px-1.5 py-0.5 text-xs font-medium tracking-wide",
        "bg-sky-500/10 text-sky-200/90",
        className,
      )}
      title="Recently added"
    >
      New
    </span>
  );
}
