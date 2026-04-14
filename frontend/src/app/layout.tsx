import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Athena PMO — AI Program Management Dashboard",
  description:
    "Real-time AI-powered program management dashboard. Monitor project health, blocked tickets, and agent actions with the Athena multi-agent system.",
  keywords: ["PMO", "AI", "Program Management", "LangGraph", "Risk Management"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ background: "var(--bg-base)" }}>{children}</body>
    </html>
  );
}
