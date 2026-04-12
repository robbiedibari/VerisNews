import React from "react";

const SunIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-5 w-5"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={2}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z"
    />
  </svg>
);

const MoonIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-5 w-5"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={2}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"
    />
  </svg>
);

function formatClock(date) {
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDate(date) {
  return date.toLocaleDateString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function Header({ darkMode, onToggleDark, now }) {
  return (
    <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800 shadow-sm h-14">
      <div className="max-w-2xl mx-auto px-4 h-full flex items-center justify-between gap-2">
        {/* Logo — oversized intentionally; pointer-events-none so overflow never blocks tabs */}
        <img
          src="/Logo_transparent.png"
          alt="Veris"
          className="h-24 sm:h-28 md:h-32 w-auto object-contain pointer-events-none dark:brightness-[3] dark:contrast-[0.8]"
        />

        {/* Live clock */}
        <div className="text-right flex-shrink-0 hidden sm:block">
          <p className="text-sm font-mono font-semibold tabular-nums text-slate-700 dark:text-slate-200 leading-none">
            {formatClock(now)}
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 leading-none">
            {formatDate(now)}
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={onToggleDark}
            aria-label="Toggle dark mode"
            className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {darkMode ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </div>
    </header>
  );
}
