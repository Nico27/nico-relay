Prompt 1:

We need to create an MVP in order to address one critical task (DASH-247): Help customers understand whether their recent activity is normal.
Customers looking at their dashboard can't tell whether this week's numbers are good, bad, or typical for them. Product wants the dashboard to help a customer answer "is this normal for us?" at a glance, without exporting data or calling their account manager.

Notes from product: probably involves comparing against some baseline, multi-location customers matter, a customer admin should be able to look at this Monday morning and act on it.

Out of scope per product: alerting/notifications, and predictive ML/forecasting. (An LLM used for explanation, summarization, or classification is not forecasting — that's fair game)
The ticket is deliberately light — that's realistic, not an oversight. Deciding what it actually means (what "normal" is, what window, what view) is part of the exercise.

In order to do this, we will define the stack:
-Backend: FastAPI with UV for managing the packages and pytest for testing.
-Frontend: React/Typescript with Vite and vitest for testing.
-Database: Postgres (we need to create a migration for schema.sql and handle seed.sql with its data accordingly since it might contain empty ranges, odd values, etc) 
-Docker: we need to align previous requirements with a docker image running with NO root user. We also need docker-compose for fast and easy development.

LLM ask:
Should we create 