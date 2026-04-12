import { useState, useCallback } from "react";

const STORAGE_KEY = "veris-read-articles";
const MAX_STORED = 500; // cap so localStorage doesn't grow unbounded

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function saveToStorage(set) {
  try {
    // Keep only the most recent MAX_STORED entries (sets preserve insertion order)
    const entries = [...set];
    const trimmed = entries.slice(-MAX_STORED);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // Storage full or unavailable — silently ignore
  }
}

export function useReadArticles() {
  const [readIds, setReadIds] = useState(loadFromStorage);

  const markRead = useCallback((id) => {
    setReadIds((prev) => {
      if (prev.has(id)) return prev;
      const next = new Set(prev);
      next.add(id);
      saveToStorage(next);
      return next;
    });
  }, []);

  const isRead = useCallback((id) => readIds.has(id), [readIds]);

  return { markRead, isRead };
}
