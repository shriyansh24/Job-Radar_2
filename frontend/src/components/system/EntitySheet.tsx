import * as React from "react";

import { cn } from "@/lib/utils";

import { Surface } from "./Surface";

type EntitySheetProps = React.HTMLAttributes<HTMLDivElement> & {
  header?: React.ReactNode;
  footer?: React.ReactNode;
};

function EntitySheet({
  className,
  header,
  footer,
  children,
  ...props
}: EntitySheetProps) {
  return (
    <Surface
      tone="default"
      padding="none"
      radius="xl"
      className={cn("overflow-hidden", className)}
      {...props}
    >
      {header ? <div className="border-b-2 border-border px-5 py-4">{header}</div> : null}
      <div className="px-5 py-5">{children}</div>
      {footer ? <div className="border-t-2 border-border px-5 py-4">{footer}</div> : null}
    </Surface>
  );
}

export { EntitySheet };
export type { EntitySheetProps };
