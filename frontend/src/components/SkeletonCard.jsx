import React from "react";

export default function SkeletonCard() {
  return (
    <div className="bg-card border border-theme rounded-xl p-4 animate-pulse">
      <div className="flex items-center gap-2 mb-3">
        <div className="h-5 w-16 bg-skel-base rounded-full" />
        <div className="h-4 w-12 bg-skel-shine rounded" />
        <div className="h-5 w-20 bg-skel-base rounded-full" />
      </div>
      <div className="space-y-2.5">
        <div className="h-4 bg-skel-base rounded w-full" />
        <div className="h-4 bg-skel-base rounded w-5/6" />
      </div>
      <div className="mt-3 space-y-2">
        <div className="h-3 bg-skel-shine rounded w-full" />
        <div className="h-3 bg-skel-shine rounded w-4/5" />
        <div className="h-3 bg-skel-shine rounded w-3/5" />
      </div>
      <div className="h-3 w-32 bg-skel-shine rounded mt-3" />
    </div>
  );
}
