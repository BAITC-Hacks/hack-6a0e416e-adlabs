import { ArrowRight, BriefcaseBusiness, Building2, Search, Target, UserRound } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { useDemo } from "../context/DemoContext";
import { useResource } from "../hooks/useResource";


function initials(name: string) {
  return name.split(" ").slice(0, 2).map((part) => part[0]).join("");
}

export function SelectorPage() {
  const { t, setEmployeeId, setRole } = useDemo();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const { data, error, loading, reload } = useResource(() => api.employees());
  const employees = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return data?.results || [];
    return (data?.results || []).filter((employee) =>
      [employee.full_name, employee.employee_id, employee.role, employee.department]
        .some((value) => value.toLowerCase().includes(normalized)),
    );
  }, [data, query]);

  function openEmployee(employeeId: string) {
    setRole("employee");
    setEmployeeId(employeeId);
    navigate(`/dashboard/${employeeId}`);
  }

  return (
    <AppShell title={t("selectEmployee")} eyebrow="Career Quest">
      <section className="selector-intro">
        <div>
          <p>{t("selectorHint")}</p>
          <label className="search-field">
            <Search size={19} aria-hidden="true" />
            <span className="sr-only">{t("search")}</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("search")} />
          </label>
        </div>
        <div className="dataset-stamp" aria-label={t("datasetSnapshot")}>
          <BriefcaseBusiness size={20} aria-hidden="true" />
          <span><strong>{data?.count || 200}</strong><small>{t("employees")}</small></span>
        </div>
      </section>

      {loading ? <LoadingState /> : null}
      {error ? <ErrorState error={error} onRetry={reload} /> : null}
      {!loading && !error && employees.length === 0 ? (
        <EmptyState title={t("noEmployees")} description={t("tryAnotherQuery")} />
      ) : null}
      {!loading && !error && employees.length > 0 ? (
        <section className="employee-grid" aria-live="polite">
          {employees.map((employee) => (
            <article className="employee-card" key={employee.employee_id}>
              <div className="employee-card-head">
                <span className="avatar" aria-hidden="true">{initials(employee.full_name)}</span>
                <span className="employee-id">{employee.employee_id}</span>
              </div>
              <div className="employee-card-copy">
                <h2>{employee.full_name}</h2>
                <p><UserRound size={15} aria-hidden="true" />{employee.role} · {employee.grade}</p>
                <p><Building2 size={15} aria-hidden="true" />{employee.department}</p>
                {employee.career_goal ? (
                  <p className="employee-goal"><Target size={15} aria-hidden="true" />{employee.career_goal.target_role} · {employee.career_goal.target_grade}</p>
                ) : null}
              </div>
              <button className="button button-secondary employee-open" type="button" onClick={() => openEmployee(employee.employee_id)}>
                {t("openProfile")}<ArrowRight size={16} aria-hidden="true" />
              </button>
            </article>
          ))}
        </section>
      ) : null}
    </AppShell>
  );
}
