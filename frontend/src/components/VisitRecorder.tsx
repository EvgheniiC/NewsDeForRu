import { useEffect } from "react";

import { startAppVisitRecording } from "../analytics/recordAppVisit";

/** Records a consented app visit once per session and Berlin day. */
export function VisitRecorder(): null {
  useEffect((): (() => void) => startAppVisitRecording(), []);
  return null;
}
