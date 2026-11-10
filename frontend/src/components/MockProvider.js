"use client";

import { useEffect, useState } from "react";

let workerPromise;

async function startWorker() {
  if (!workerPromise) {
    workerPromise = import("../../mocks/browser").then(
      async ({ worker }) => {
        await worker.start({
          onUnhandledRequest: "bypass",
        });
      }
    );
  }

  return workerPromise;
}

export default function MockProvider({ children }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    async function initialize() {
      if (process.env.NEXT_PUBLIC_API_MOCKS === "true") {
        await startWorker();
      }

      setReady(true);
    }

    initialize().catch(console.error);
  }, []);

  if (!ready) return null;

  return children;
}