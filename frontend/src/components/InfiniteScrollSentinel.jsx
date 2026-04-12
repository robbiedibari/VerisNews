import React, { useEffect, useRef } from "react";

/**
 * Invisible div at the bottom of the feed.
 * Calls onIntersect() when scrolled into view.
 */
export default function InfiniteScrollSentinel({ onIntersect, enabled }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!enabled) return;
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) onIntersect();
      },
      { rootMargin: "200px" }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [enabled, onIntersect]);

  return <div ref={ref} className="h-1" />;
}
