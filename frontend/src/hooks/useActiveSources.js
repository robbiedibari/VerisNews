import { useState, useEffect } from "react";

const API = process.env.REACT_APP_API_URL || "/api";

// "Top Stories" and "All" are always visible regardless of DB content
const ALWAYS_VISIBLE = new Set(["Top Stories", "All"]);

export function useActiveSources() {
  const [activeSources, setActiveSources] = useState(null); // null = still loading

  useEffect(() => {
    fetch(`${API}/sources`)
      .then((r) => r.json())
      .then((data) => setActiveSources(new Set(data.sources)))
      .catch(() => setActiveSources(null)); // on error show all tabs
  }, []);

  /**
   * Returns true if the given tab should be rendered.
   * While loading (activeSources === null) all tabs are shown to avoid layout flash.
   */
  const isVisible = (source) =>
    ALWAYS_VISIBLE.has(source) ||
    activeSources === null ||
    activeSources.has(source);

  return { isVisible, activeSources };
}
