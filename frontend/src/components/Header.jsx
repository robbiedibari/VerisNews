import React from "react";

const SunIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
  </svg>
);

const MoonIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
  </svg>
);

const BookIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const THEME_META = {
  light: { icon: <SunIcon />,  label: "Light mode",  next: "sepia" },
  sepia: { icon: <BookIcon />, label: "Sepia mode",  next: "dark"  },
  dark:  { icon: <MoonIcon />, label: "Dark mode",   next: "light" },
};

function formatClock(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatDate(date) {
  return date.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric", year: "numeric" });
}

export default function Header({ theme, onCycleTheme, now }) {
  const meta = THEME_META[theme] ?? THEME_META.light;

  return (
    <header className="sticky top-0 z-30 bg-header backdrop-blur border-b border-header shadow-sm h-14 overflow-hidden transition-colors duration-250">
      <div className="max-w-2xl mx-auto px-4 h-full flex items-center justify-between gap-2">

        {/* Logo — oversized intentionally; pointer-events-none so overflow never blocks tabs */}
        <img
          src="/Logo_transparent.png"
          alt="Veris"
          className={`h-24 sm:h-28 md:h-32 w-auto object-contain pointer-events-none
            ${theme === "dark" ? "brightness-[3] contrast-[0.8]" : ""}
            ${theme === "sepia" ? "sepia-[0.3] brightness-[0.85]" : ""}`}
        />

        {/* Live clock */}
        <div className="text-right flex-shrink-0 hidden sm:block">
          <p className="text-sm font-mono font-semibold tabular-nums text-primary leading-none">
            {formatClock(now)}
          </p>
          <p className="text-xs text-muted mt-0.5 leading-none">
            {formatDate(now)}
          </p>
        </div>

        {/* Theme cycle button */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={onCycleTheme}
            aria-label={`Switch to ${meta.next} mode`}
            title={meta.label}
            className="p-2 rounded-lg text-muted hover:bg-tab-pill transition-colors"
          >
            {meta.icon}
          </button>
        </div>

      </div>
    </header>
  );
}
