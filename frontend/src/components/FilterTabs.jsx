import React from "react";

export const SOURCES = ["Top Stories", "All", "AP", "AFP", "NPR", "BBC", "DW", "NHK", "ABC", "CBC", "RFI", "PBS"];

// Each source gets a distinct active colour so users can spot the filter at a glance
const SOURCE_COLORS = {
  "Top Stories": "data-[active=true]:bg-amber-500  data-[active=true]:text-white",
  All: "data-[active=true]:bg-slate-800  data-[active=true]:text-white dark:data-[active=true]:bg-slate-100 dark:data-[active=true]:text-slate-900",
  AP:  "data-[active=true]:bg-blue-800   data-[active=true]:text-white",
  AFP: "data-[active=true]:bg-green-700  data-[active=true]:text-white",
  NPR: "data-[active=true]:bg-indigo-600 data-[active=true]:text-white",
  BBC: "data-[active=true]:bg-red-700    data-[active=true]:text-white",
  DW:  "data-[active=true]:bg-amber-500  data-[active=true]:text-white",
  NHK: "data-[active=true]:bg-rose-600   data-[active=true]:text-white",
  ABC: "data-[active=true]:bg-teal-600   data-[active=true]:text-white",
  CBC: "data-[active=true]:bg-purple-700 data-[active=true]:text-white",
  RFI: "data-[active=true]:bg-orange-600 data-[active=true]:text-white",
  PBS: "data-[active=true]:bg-emerald-700 data-[active=true]:text-white",
};

export default function FilterTabs({ active, onChange }) {
  return (
    <div className="relative z-20 max-w-2xl mx-auto px-4 pt-3 pb-1">
      <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
        {SOURCES.map((src) => (
          <button
            key={src}
            data-active={active === src}
            onClick={() => onChange(src)}
            className={`
              flex-shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-all
              bg-slate-100 dark:bg-slate-800
              text-slate-600 dark:text-slate-300
              hover:bg-slate-200 dark:hover:bg-slate-700
              ${SOURCE_COLORS[src] ?? ""}
            `}
          >
            {src === "Top Stories" ? "🏆 Top Stories" : src}
          </button>
        ))}
      </div>
    </div>
  );
}
