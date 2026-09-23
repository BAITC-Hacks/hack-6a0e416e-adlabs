import { Check, Flag, MoveRight, Sparkles } from "lucide-react";

import { useDemo } from "../context/DemoContext";
import type { CareerNode } from "../types";


export function CareerRoute({ nodes }: { nodes: CareerNode[] }) {
  const { t } = useDemo();
  const labels = { current: t("currentNode"), target: t("targetNode"), future: t("futureNode") };
  const icons = { current: Check, target: Flag, future: Sparkles };

  return (
    <div className="career-route" aria-label={t("careerRoute") }>
      {nodes.map((node, index) => {
        const Icon = icons[node.kind];
        return (
          <div className="career-route-segment" key={`${node.kind}-${node.label}`}>
            <div className={`career-node career-node-${node.kind}`}>
              <span className="career-node-icon"><Icon size={18} aria-hidden="true" /></span>
              <span>
                <small>{labels[node.kind]}</small>
                <strong>{node.role}</strong>
                <em>{node.grade}</em>
              </span>
            </div>
            {index < nodes.length - 1 ? <MoveRight className="career-route-arrow" aria-hidden="true" /> : null}
          </div>
        );
      })}
    </div>
  );
}
