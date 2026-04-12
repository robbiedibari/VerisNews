import { useState, useEffect } from "react";

/**
 * Returns the current Date and re-renders on the given interval.
 * Default: every second (good for a live clock).
 * Pass 60_000 if you only need minute-level updates.
 */
export function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return now;
}
