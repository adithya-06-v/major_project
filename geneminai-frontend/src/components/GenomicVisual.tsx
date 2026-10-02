const BASES = ["A", "T", "C", "G", "A", "G", "T", "C"];

export function GenomicVisual() {
  return (
    <div className="genomic-visual" aria-hidden="true">
      <div className="genomic-orbit genomic-orbit-one" />
      <div className="genomic-orbit genomic-orbit-two" />
      <div className="helix">
        {BASES.map((base, index) => (
          <div className="helix-row" style={{ "--row": index } as React.CSSProperties} key={`${base}-${index}`}>
            <span className="helix-node">{base}</span>
            <span className="helix-bridge" />
            <span className="helix-node">{BASES[BASES.length - index - 1]}</span>
          </div>
        ))}
      </div>
      <div className="sequence-stream sequence-stream-top">ATG · GTG · CAT · CTG · ACT · CCT</div>
      <div className="sequence-stream sequence-stream-bottom">K-MER 03 / HBB LOCUS / RF</div>
      {[0, 1, 2, 3, 4].map((particle) => (
        <span className={`genomic-particle particle-${particle}`} key={particle} />
      ))}
    </div>
  );
}
