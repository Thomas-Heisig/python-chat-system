import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { RightSidebar } from "./RightSidebar";

describe("RightSidebar sources tree", () => {
  it("groups sources by hierarchical project path", () => {
    render(
      <RightSidebar
        collapsed={false}
        activeTab="sources"
        selectedSourceId={2}
        sources={[
          {
            id: 1,
            file: "angebot-klaener-lemwerder.md",
            position: "Zeile 1",
            relevance: "95%",
            projectLabel: "Heisig Naturstein / Angebote / Kläner",
            scopeDepth: 2,
          },
          {
            id: 2,
            file: "angebote-vorlage.md",
            position: "Zeile 8",
            relevance: "81%",
            projectLabel: "Heisig Naturstein / Angebote",
            scopeDepth: 1,
          },
          {
            id: 3,
            file: "naturstein-uebersicht.md",
            position: "Zeile 2",
            relevance: "73%",
            projectLabel: "Heisig Naturstein",
            scopeDepth: 0,
          },
        ]}
        activeProjectLabel="Heisig Naturstein / Angebote / Kläner"
        users={[]}
        currentUserId={1}
        currentUserIsAdmin={false}
        locale="de-DE"
        timezone="Europe/Berlin"
        contextUsage={null}
        onToggleCollapse={() => undefined}
        onChangeTab={() => undefined}
        onContextInspect={() => undefined}
      />,
    );

    expect(screen.getByRole("button", { name: "Quellengruppe schliessen: Heisig Naturstein" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Quellengruppe schliessen: Angebote" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Quellengruppe schliessen: Kläner" })).toBeTruthy();
    expect(screen.getByText("angebot-klaener-lemwerder.md")).toBeTruthy();
    expect(screen.getByText("angebote-vorlage.md")).toBeTruthy();
    expect(screen.getByText("naturstein-uebersicht.md")).toBeTruthy();
  });
});
