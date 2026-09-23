import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api";


describe("API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends employee scope headers to protected endpoints", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ employee: { employee_id: "E0001" } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await api.dashboard("E0001");

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Headers;
    expect(url).toBe("http://localhost:8000/api/v1/employees/E0001/dashboard/");
    expect(headers.get("X-Demo-Role")).toBe("employee");
    expect(headers.get("X-Employee-ID")).toBe("E0001");
  });

  it("exposes the backend error message and status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ error: { message: "Access denied" } }),
      }),
    );

    await expect(api.dashboard("E0002")).rejects.toMatchObject({
      message: "Access denied",
      status: 403,
    });
  });
});
