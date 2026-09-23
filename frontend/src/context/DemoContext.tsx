import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import { translate } from "../i18n";
import type { DemoRole, Language } from "../types";


interface DemoContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  role: DemoRole;
  setRole: (role: DemoRole) => void;
  employeeId: string | null;
  setEmployeeId: (employeeId: string | null) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const DemoContext = createContext<DemoContextValue | null>(null);

function readLanguage(): Language {
  const stored = localStorage.getItem("career-quest-language");
  return stored === "en" || stored === "kk" ? stored : "ru";
}

export function DemoProvider({ children }: { children: ReactNode }) {
  const [language, updateLanguage] = useState<Language>(readLanguage);
  const [role, updateRole] = useState<DemoRole>("employee");
  const [employeeId, updateEmployeeId] = useState<string | null>(
    localStorage.getItem("career-quest-employee"),
  );

  const value = useMemo<DemoContextValue>(
    () => ({
      language,
      setLanguage: (next) => {
        localStorage.setItem("career-quest-language", next);
        updateLanguage(next);
      },
      role,
      setRole: updateRole,
      employeeId,
      setEmployeeId: (next) => {
        if (next) localStorage.setItem("career-quest-employee", next);
        else localStorage.removeItem("career-quest-employee");
        updateEmployeeId(next);
      },
      t: (key, params) => translate(language, key, params),
    }),
    [employeeId, language, role],
  );

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemo(): DemoContextValue {
  const value = useContext(DemoContext);
  if (!value) throw new Error("useDemo must be used inside DemoProvider");
  return value;
}
