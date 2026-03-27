import * as React from "react";

import { cn } from "@/lib/utils";

import { Surface } from "./Surface";

type DataListProps = React.HTMLAttributes<HTMLDivElement> & {
  header?: React.ReactNode;
  footer?: React.ReactNode;
};

function DataList({
  className,
  header,
  footer,
  children,
  ...props
}: DataListProps) {
  return (
    <Surface tone="default" padding="none" radius="xl" className={className} {...props}>
      {header ? <div className="border-b-2 border-border px-5 py-4">{header}</div> : null}
      <div className={cn("divide-y-2 divide-border", !children && "min-h-24")}>{children}</div>
      {footer ? <div className="border-t-2 border-border px-5 py-4">{footer}</div> : null}
    </Surface>
  );
}

export { DataList };
export type { DataListProps };
