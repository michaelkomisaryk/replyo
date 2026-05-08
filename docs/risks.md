# Risks

## Instagram API Limits

Meta's Graph API has strict rate limits and requires app review for DM access. If the app is rejected or rate-limited, message sync could break or be delayed.

**Mitigation:** Apply for advanced access early; implement queue-based sync with retry logic; inform users of limitations upfront.

## Synchronization Issues

Real-time message sync depends on webhooks from Instagram. If webhooks fail or messages arrive out of order, the dashboard could show stale data or miss messages entirely.

**Mitigation:** Implement webhook verification, message deduplication, and a fallback polling mechanism for reliability.

## Complex Setup

Connecting Instagram via OAuth and Meta's API can be confusing for non-technical shop owners. A bad onboarding experience could cause drop-off before the product is even used.

**Mitigation:** Build a guided step-by-step onboarding flow with screenshots and clear error messages. Provide support docs and a short video walkthrough.
