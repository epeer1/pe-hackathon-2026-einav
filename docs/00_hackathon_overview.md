# MLH Production Engineering Hackathon 2026 Overview

## Event Summary
An MLH Production Engineering Hackathon aimed at taking a minimal starter template (Flask + Peewee) and building a highly concurrent "Flash Sale" Ticket Reservation System that can be trusted to not oversell inventory under heavy pressure.

## Official Links
- **Event Site:** [mlh-pe-hackathon.com](https://mlh-pe-hackathon.com/)
- **Devpost:** [pe-hackathon.devpost.com](https://pe-hackathon.devpost.com/)
- **Registration:** [events.mlh.io/events/13606](https://events.mlh.io/events/13606)
- **Official Template Repo:** [GitHub - PE-Hackathon-Template-2026](https://github.com/MLH-Fellowship/PE-Hackathon-Template-2026)

## Dates and Key Checkpoints
- **Start:** Friday, April 3, 2026, 7:00 PM EDT (Opening Ceremony)
- **CI/CD Workshop:** During hackathon window (Check Devpost schedule)
- **Initial Submission Due:** TBD (Check final Devpost updates)
- **Final Submission Due:** Sunday, April 5, 2026, 1:00 PM EDT
- *Note: Ensure your code and demo are finalized well before Sunday 1:00 PM EDT to avoid submission rush.*

## Participation Constraints
- **Public Repo Required:** The GitHub repository must be public.
- **Demo Video:** A demo video of 2 minutes or less must be submitted.
- **Continual Availability:** Code and video must remain public indefinitely to stay prize-eligible.
- **Timing Constraint:** Video must be created *during* the hackathon weekend.
- **Prior Work Rule:** Project must *not* include prior work; it must be started and developed during the hackathon.
- **Submissions:** One project submission per team.
- **Eligibility:** Only team projects are eligible for prizes.

## Submission Requirements
1. Valid link to a public GitHub repository.
2. Link to a newly recorded demo video (≤ 2 minutes).
3. Clear documentation in the README matching Devpost requirements.

## Project Concept Summary
Our team is starting from the official Flask/Peewee template and building a High-Concurrency Flash Sale / Ticket Reservation API. To structure our hackathon weekend perfectly, we have organized our development tracking into clear "Bronze", "Silver", and "Gold" milestones that build on each sequentially. We must establish the naive "Bronze" functionality first before moving on to complex concurrency locks.

## Reliability Quest Notes
If choosing the Reliability roadmap, the core goal is ensuring the service doesn't fall over. The emphasis is on:
- Adding tests.
- Implementing health checks.
- Handling graceful failure (error responses, retry logic, timeouts).
- Designing the API so your team can trust it under stress condition.

## Known Facts
- We *must* use the starter template.
- The starter leverages Flask, Peewee ORM, PostgreSQL, and `uv`.
- A 2-minute limit strictly applies for the demo.
- No prior work is permitted.

## Unconfirmed Items
- Exact workshop timing and content (check schedule day-of).
- Specific criteria distinguishing Silver from Gold tiers.

## Practical Implications for Our Team
- Our repository `pe-hackathon-2026-einav` needs to eventually be made public.
- We must build standard boilerplate (models, routes, logic) on top of the Flask starter rather than starting from scratch.
- We must emphasize a working base (Bronze) immediately, and commit everything cleanly across the weekend.
- We should script our demo video on Saturday to ensure it hits the 2-minute mark perfectly on Sunday morning.
