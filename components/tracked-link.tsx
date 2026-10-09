"use client";

import Link from "next/link";
import type { ComponentProps } from "react";
import { captureEvent } from "@/lib/analytics-client";

type Props = ComponentProps<typeof Link> & {
  event: string;
  eventProperties?: Parameters<typeof captureEvent>[1];
};

/** A regular link with an explicit analytics event for conversion funnels. */
export function TrackedLink({ event, eventProperties, onClick, ...props }: Props) {
  return <Link {...props} onClick={(e) => {
    onClick?.(e);
    if (!e.defaultPrevented) captureEvent(event, eventProperties);
  }} />;
}
