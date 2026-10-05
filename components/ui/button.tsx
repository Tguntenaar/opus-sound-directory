import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost" | "outline";
  size?: "sm" | "md";
};

export function Button({
  className,
  variant = "default",
  size = "md",
  ...props
}: Props) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-400 disabled:opacity-50",
        size === "sm" ? "px-2.5 py-1.5 text-sm" : "px-4 py-2 text-sm",
        variant === "default" &&
          "bg-violet-500 text-white hover:bg-violet-400 active:bg-violet-600",
        variant === "ghost" && "text-zinc-300 hover:bg-zinc-800/80",
        variant === "outline" &&
          "border border-zinc-700 text-zinc-200 hover:border-zinc-500 hover:bg-zinc-900",
        className,
      )}
      {...props}
    />
  );
}
