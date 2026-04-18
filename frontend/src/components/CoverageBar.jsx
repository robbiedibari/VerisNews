import React from "react";

/**
 * Shows which other sources independently reported the same story.
 * Only renders when 2+ sources covered the event — single-source stories
 * show nothing (absence of the bar is itself informative).
 */
export default function CoverageBar({ coveredBy }) {
  if (!coveredBy || coveredBy.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 mt-2.5 flex-wrap">
      <span className="text-[10px] font-semibold uppercase tracking-widest text-muted">
        Also:
      </span>
      {coveredBy.map((source) => (
        <span
          key={source}
          className="text-[10px] font-bold uppercase tracking-wide
            text-muted border border-theme rounded px-1.5 py-0.5
            leading-none"
        >
          {source}
        </span>
      ))}
    </div>
  );
}
