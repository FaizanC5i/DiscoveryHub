/**
 * The floating workspace illustration (cards, AI tile, glows). Pure decoration: drawn with
 * CSS from auth-landing.css. The cards drift gently up and down; it moves to the left when
 * the sign-in panel opens.
 */
export function WorkspaceIllustration({ signIn }: { signIn: boolean }) {
  return (
    <div
      className={`dhl-workspace-positioner ${signIn ? "dhl-workspace-positioner--signin" : ""}`}
      aria-hidden="true"
    >
      <div className="dhl-workspace">
        <div className="dhl-workspace__halo" />
        <div className="dhl-workspace__orbit" />
        <div className="dhl-ai-beams">
          <i />
          <i />
          <i />
        </div>
        <div className="dhl-workspace__ground" />

        <div className="dhl-float-card dhl-float-card--sync">
          <div className="dhl-sync-block" />
          <div className="dhl-sync-lines">
            <i />
            <i />
            <i />
          </div>
          <small>Synced</small>
        </div>

        <div className="dhl-float-card dhl-float-card--velocity">
          <b>PROJECT VELOCITY</b>
          <div className="dhl-velocity-chart">
            <span style={{ height: "18%" }} />
            <span style={{ height: "45%" }} />
            <span style={{ height: "36%" }} />
            <span style={{ height: "76%" }} />
          </div>
          <div className="dhl-velocity-line">
            <i />
            <i />
            <i />
            <i />
          </div>
        </div>

        <div className="dhl-float-card dhl-float-card--artefact">
          <i className="dhl-artefact-dot" />
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative SVG from the design */}
          <img src="/landing/artefact.svg" alt="" />
          <small>Artefacts</small>
        </div>

        <div className="dhl-workspace__decks">
          <div className="dhl-deck dhl-deck--back" />
          <div className="dhl-deck dhl-deck--middle" />
          <div className="dhl-deck dhl-deck--top" />
        </div>

        <div className="dhl-ai-card">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/landing/sparkle.svg" alt="" />
          <small>AI</small>
        </div>

        <div className="dhl-status-pill dhl-status-pill--knowledge">
          <i />
          Knowledge
        </div>
        <div className="dhl-status-pill dhl-status-pill--insight">
          <i />
          Live insight
        </div>
      </div>
    </div>
  );
}
