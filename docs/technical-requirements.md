# Technical Requirements

## Frontend

- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** Zustand or React Query
- **Auth:** NextAuth.js

## Backend

- **Runtime:** Node.js
- **Framework:** Express.js or Fastify
- **Language:** TypeScript
- **Architecture:** Clean architecture with feature-based structure
- **ORM:** Prisma

## Database

- **Primary DB:** PostgreSQL
- **Migrations:** Prisma Migrate

## Infrastructure

- **Hosting:** Vercel (frontend), Railway or Render (backend)
- **Environment:** .env files with separate configs for dev/prod

## Integrations

- **Instagram API:** Meta Graph API for reading and sending DMs
- **Webhooks:** For real-time message sync from Instagram

## Code Standards

- TypeScript everywhere — no plain JS
- Clean architecture — separation of concerns
- Feature-based folder structure
- Reusable components
- Server Actions where possible
