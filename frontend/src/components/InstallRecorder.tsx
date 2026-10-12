import { useEffect } from "react";

import { startAppInstallRecording } from "../analytics/recordAppInstall";

/** Records a consented Android install once per device. */
export function InstallRecorder(): null {
  useEffect((): (() => void) => startAppInstallRecording(), []);
  return null;
}
