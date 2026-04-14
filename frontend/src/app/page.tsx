"use client";

import { useState, useCallback } from "react";
import TopNav from "@/components/TopNav";
import ChatPanel from "@/components/ChatPanel";
import MetricsPanel from "@/components/MetricsPanel";
import ATLPanel from "@/components/ATLPanel";
import RiskFeed from "@/components/RiskFeed";
import type { ATLEntry } from "@/lib/types";

export default function Dashboard() {
  const [resetKey, setResetKey] = useState(0);
  const [neo4jTotal, setNeo4jTotal] = useState(0);
  const [vectorCount, setVectorCount] = useState(0);
  const [liveATLEntries, setLiveATLEntries] = useState<ATLEntry[]>([]);

  const handleNewChat = useCallback(() => {
    setResetKey((k) => k + 1);
  }, []);

  const handleMetricsLoaded = useCallback((neo4j: number, vectors: number) => {
    setNeo4jTotal(neo4j);
    setVectorCount(vectors);
  }, []);

  const handleNewATLEntries = useCallback((entries: ATLEntry[]) => {
    setLiveATLEntries(entries);
  }, []);

  const navHeight = 56;
  const panelHeight = `calc(100vh - ${navHeight}px)`;

  return (
    <>
      <TopNav
        onNewChat={handleNewChat}
        neo4jTotal={neo4jTotal}
        vectorCount={vectorCount}
      />

      {/* 3-Column Dashboard Grid */}
      <main
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 1.2fr 1.2fr",
          gridTemplateRows: "1fr",
          height: panelHeight,
          gap: "12px",
          padding: "12px",
          overflow: "hidden",
          background: "var(--bg-base)",
        }}
      >
        {/* Column 1: AI Chat (full height) */}
        <div style={{ minHeight: 0, overflow: "hidden" }}>
          <ChatPanel
            resetKey={resetKey}
            onNewATLEntries={handleNewATLEntries}
          />
        </div>

        {/* Column 2: Metrics (top 40%) + ATL (bottom 60%) */}
        <div
          style={{
            display: "grid",
            gridTemplateRows: "2fr 3fr",
            gap: "12px",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          <div style={{ minHeight: 0, overflow: "hidden" }}>
            <MetricsPanel onMetricsLoaded={handleMetricsLoaded} />
          </div>
          <div style={{ minHeight: 0, overflow: "hidden" }}>
            <ATLPanel newEntries={liveATLEntries} />
          </div>
        </div>

        {/* Column 3: Risk Feed (full height) */}
        <div style={{ minHeight: 0, overflow: "hidden" }}>
          <RiskFeed />
        </div>
      </main>
    </>
  );
}
