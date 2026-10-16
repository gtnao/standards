import { Title } from "@mantine/core";
import type { ReactNode } from "react";
import classes from "./page-frame.module.css";

type Props = {
  title: string;
  actions?: ReactNode;
  children?: ReactNode;
};

// A flush, sticky title bar over the grey content area; both are separated by 1px lines only.
export function PageFrame({ title, actions, children }: Props) {
  return (
    <>
      <header className={classes.header}>
        <Title order={1}>{title}</Title>
        {actions}
      </header>
      <div className={classes.body}>{children}</div>
    </>
  );
}
