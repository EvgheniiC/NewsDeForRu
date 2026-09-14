import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { ServerPipelinePanels } from "./ServerPipelinePanels";
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

test("ServerPipelinePanels shows health status and pipeline run for staff", () => {
  render(
    <ServerPipelinePanels
      canRunPipeline={true}
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

  expect(screen.getByRole("heading", { name: "Состояние сервера" })).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Последний ручной запуск pipeline" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Обновить через pipeline" })).toBeTruthy();
});

test("ServerPipelinePanels hides pipeline run when the account cannot start it", () => {
  render(
    <ServerPipelinePanels
      canRunPipeline={false}
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

  expect(screen.getByRole("heading", { name: "Состояние сервера" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Последний ручной запуск pipeline" })).toBeNull();
});
