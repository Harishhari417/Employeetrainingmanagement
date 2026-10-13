import { useState } from "react";

export default function LogoPlaceholder() {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div className="flex h-12 min-w-12 items-center justify-center rounded-xl bg-indigo-600 px-2 text-xs font-bold text-white">
        EVIG
      </div>
    );
  }
  return (
    <img
      src="/EVIG-Intergration_horizantal_Logo_1500-1.png"
      alt="EVIG Integration"
      onError={() => setFailed(true)}
      className="h-12 w-auto max-w-[220px] object-contain"
    />
  );
}
