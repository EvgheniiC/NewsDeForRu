import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { FeedDevPanels } from "./FeedDevPanels";
import type { HealthResponse } from "../types/pipeline";

afterEach(() => {
  cleanup();
});

const HEALTH_OK: HealthResponse = {
  status: "ok",
  database: "ok",
  last_pipeline_run_at: "2026-09-13T08:03:10Z",
  last_pipeline_ok: true,
  last_pipeline_run_id: "fd9c898a-7ff3-45d3-8c75-9d667cfd094f",
  pipeline_scheduler: "enabled"
};

test("FeedDevPanels stays collapsed so the feed keeps viewport height", () => {
  render(
    <FeedDevPanels
      health={HEALTH_OK}
      healthError=""
      lastManualRun={null}
      pipelineHttpError=""
      pipelineNetworkError=""
      pipelineOkMessage={null}
      pipelineRunning={false}
      onRefresh={() => undefined}
    />
  );

  const summary: HTMLElement = screen.getByText("Сервер и pipeline");
  const details: HTMLDetailsElement = summary.closest("details") as HTMLDetailsElement;
  expect(details.open).toBe(false);
  expect(summary.querySelector(".health-ok")?.textContent).toBe("ok");
});
