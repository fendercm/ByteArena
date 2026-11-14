"use client";

import { useEffect, useState } from "react";

const mocksEnabled = process.env.NEXT_PUBLIC_API_MOCKS === "true";

let workerPromise;

async function startWorker() {
  if (!workerPromise) {
    workerPromise = import("../../mocks/browser").then(async ({ worker }) => {
      await worker.start({
        onUnhandledRequest: "bypass",
      });
    });
  }

  return workerPromise;
}

export default function MockProvider({ children }) {
  const [ready, setReady] = useState(!mocksEnabled);

  useEffect(() => {
    if (!mocksEnabled) return;

    startWorker()
      .then(() => setReady(true))
      .catch((error) => {
        console.error("MSW worker failed to start:", error);
        // Do not leave the whole application hidden if mocks fail.
        setReady(true);
      });
  }, []);

  if (mocksEnabled && !ready) return null;

  return children;
}
