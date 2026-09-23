import { describe, expect, it } from "vitest";

import { messages, translate } from "./i18n";


describe("translations", () => {
  it("serves the primary navigation in all supported languages", () => {
    expect(translate("ru", "dashboard")).toBe("Обзор");
    expect(translate("en", "dashboard")).toBe("Dashboard");
    expect(translate("kk", "dashboard")).toBe("Шолу");
  });

  it("falls back predictably for unknown keys", () => {
    expect(translate("ru", "unknown-key")).toBe("unknown-key");
  });

  it("keeps the RU, EN and KZ dictionaries in sync", () => {
    const englishKeys = Object.keys(messages.en).sort();
    expect(Object.keys(messages.ru).sort()).toEqual(englishKeys);
    expect(Object.keys(messages.kk).sort()).toEqual(englishKeys);
  });
});
