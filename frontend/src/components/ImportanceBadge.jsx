import React from "react";

/**
 * Clean editorial importance label — no emoji, no pills, no backgrounds.
 * Standard and Low are not shown — their absence implies routine news.
 * Breaking and Critical are the only levels that demand attention.
 */

const LEVELS = {
  Breaking:  { color: "text-red-600 dark:text-red-500",      label: "BREAKING"  },
  Critical:  { color: "text-orange-600 dark:text-orange-500", label: "CRITICAL"  },
  Important: { color: "text-amber-600 dark:text-amber-500",   label: "IMPORTANT" },
  Standard:  null,
  Low:       null,
};

export default function ImportanceBadge({ level }) {
  const meta = LEVELS[level];
  if (!meta) return null;

  return (
    <span className={`text-[10px] font-black uppercase tracking-widest leading-none ${meta.color}`}>
      {meta.label}
    </span>
  );
}
