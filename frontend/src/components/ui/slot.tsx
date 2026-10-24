import * as React from "react";

import { cn } from "@/lib/utils";

/** Minimal "asChild" helper: passes className and props onto the single child element (e.g. a Link). */
export const Slot = React.forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }>(
  ({ children, className, ...props }, ref) => {
    if (!React.isValidElement(children)) return null;
    const child = children as React.ReactElement<{ className?: string }>;
    return React.cloneElement(child, {
      ...props,
      ...child.props,
      className: cn(className, child.props.className),
      ref,
    } as React.Attributes & { className?: string });
  },
);
Slot.displayName = "Slot";
