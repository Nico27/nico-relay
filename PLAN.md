We need to create an MVP in order to address one critical task (DASH-247): Help customers understand whether their recent activity is normal.

Out of scope per product: alerting/notifications, and predictive ML/forecasting. (An LLM used for explanation, summarization, or classification is not forecasting — that's fair game)
The ticket is deliberately light — that's realistic, not an oversight. Deciding what it actually means (what "normal" is, what window, what view) is part of the exercise.

In order to do this, we will define the stack as followed:
-LLM/Harness: Deepseek V4.1 Flash running on Gentle-AI.
-Backend: FastAPI with UV for managing the packages and pytest for testing.
-Frontend: React/Typescript with Vite and vitest for testing.
-Database: Postgres (we need to create a migration for schema.sql and handle seed.sql with its data accordingly since it might contain empty ranges, odd values, etc)
-Docker: we have to align previous requirements with a docker image running with NO root user. We also need docker-compose for fast and easy development.

Since I will be using Gentle-AI (https://github.com/Gentleman-Programming/gentle-ai), I will be using the ODD approach over SDD.
Why ODD instead of SDD? To keep it simple. This new approach allows me to work with small pieces of changes instead of huge ones.
In general, when I used to worked with SDD, the approach plans everything for me prior develop anything. And at the end, when we have all build if something was not correct or we don't like it, SDD forces you to plan all again and start from scratch.
This is what ODD resolves, working with small changes that you can control, test and plan while developing.
ODD also applies test-first development: capture a failing behavior test before implementation, make it pass, then refactor while tests stay green.

More about ODD: https://github.com/Gentleman-Programming/gentle-ai#odd--keep-small-work-small

Besides ODD, Gentle-AI also provides RDD for free, so it will be also used in the project.

More about RDD: https://github.com/Gentleman-Programming/gentle-ai#rdd--check-finished-work-at-the-right-depth