import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { DemoProvider } from "../context/DemoContext";
import { CoachPage } from "./CoachPage";


describe("CoachPage", () => {
  it("mounts and unmounts when scrollIntoView is asynchronous", () => {
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: vi.fn(() => Promise.resolve()),
    });

    const view = render(
      <MemoryRouter initialEntries={["/coach/E0001"]}>
        <DemoProvider>
          <Routes>
            <Route path="/coach/:employeeId" element={<CoachPage />} />
          </Routes>
        </DemoProvider>
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText("Задайте вопрос о следующем карьерном шаге")).toBeInTheDocument();
    expect(() => view.unmount()).not.toThrow();
  });
});
