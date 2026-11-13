import type { Metadata } from "next";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "./globals.css";
import "./integration.css";
import { AppProvider } from "@/components/provider";

export const metadata: Metadata = {
  title: {
    default: "Presence — Show up. Be recognized.",
    template: "%s · Presence",
  },
  description:
    "A considered space for face recognition attendance. Explore the interactive Presence frontend and attendance workspace.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
