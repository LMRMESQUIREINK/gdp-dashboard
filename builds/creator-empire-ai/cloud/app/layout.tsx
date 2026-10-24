import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Creator Empire AI -- Cloud Edition",
  description: "One product image. One finished campaign. Cloud Edition (not deployed -- see README.md).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
