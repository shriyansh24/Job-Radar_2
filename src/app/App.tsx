import React from "react";
import { RouterProvider } from "react-router";
import { router } from "./routes";
import { ThemeProvider } from "./theme-provider";

export default function App() {
  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}