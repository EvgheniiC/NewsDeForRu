import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";

import { UrgentBrief } from "./UrgentBrief";

afterEach((): void => {
  cleanup();
});

describe("urgent brief", () => {
  test("shows the three labels and hides an empty line", () => {
    render(
      <UrgentBrief
        actionToday=""
        affects={"- Арендаторы\n- Собственники"}
        happened="С сегодняшнего дня меняется срок подачи."
      />
    );

    expect(screen.getByText(/С сегодняшнего дня/)).toBeTruthy();
    expect(screen.getByText("Кого касается")).toBeTruthy();
    expect(screen.getByText("Арендаторы")).toBeTruthy();
    expect(screen.getByText("Собственники")).toBeTruthy();
    expect(screen.queryByText("Что сделать сегодня")).toBeNull();
  });

  test("renders nothing when every line is empty", () => {
    const { container } = render(<UrgentBrief actionToday="" affects="" happened="" />);
    expect(container.textContent).toBe("");
  });
});
