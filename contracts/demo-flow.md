# Career Quest Demo Flow

Target duration: 4-5 minutes.

1. **Employee selection** - open the app and choose `E0001`. Mention that all 200 profiles come from the supplied dataset.
2. **Dashboard** - show the target role, weighted readiness, critical gaps, next best quest, career route, XP, rank, and achievements.
3. **Explainability** - open the recommended quest and point to the three explanation groups: goal match, skill impact, and participation history.
4. **Quest chain** - open Quests. Show that locked events include up to three steps and that prerequisites cannot be bypassed through the API.
5. **Live recalculation** - start and complete `EV_005`. The backend writes one demo history item, awards XP once, updates effective skills, and recalculates readiness and recommendations.
6. **AI Coach** - ask why the next quest is recommended and what should be completed first. Switch RU/EN/KZ to show localized deterministic answers.
7. **Career goal** - open Career, choose another valid role/grade pair, save, and show the recalculated route and gaps.
8. **HR mode** - switch to HR. Show top aggregate gaps, participation statuses, employees without goals, and employees without an eligible next step. Emphasize that there is no public employee ranking.

Recovery path: if local state was changed during rehearsal, restart with `python backend/manage.py import_career_dataset --reset-demo-state` or recreate the Compose volume.
