# Smart Chat Visibility

## Overview

Not all chats should be shown at the same time. Smart Chat Visibility controls which conversations appear in the main dashboard view, in what order, and when they get hidden or archived.

## Priority Order

Chats are displayed in the following order from top to bottom:

1. **New Clients** — never replied to
2. **Waiting for Reply** — no response in over 1 hour
3. **Active Orders** — open order in progress
4. **Completed Orders** — shown for 24 hours after completion, then archived
5. **Rejected Clients** — hidden by default, accessible via filter

## Active vs Inactive Logic

### Active Chat
A chat is considered **active** if:
- A message was sent or received in the last 7 days
- An order linked to the chat is still open
- The chat has been manually pinned by a manager

Active chats appear in the main dashboard view.

### Inactive Chat
A chat becomes **inactive** if:
- No messages in the last 7 days
- Order is completed or rejected
- Manually archived by a manager

Inactive chats are moved to the archive and hidden from the main view. They remain searchable and can be reactivated when a client messages again.

## Auto-Reactivation

If an inactive or archived client sends a new message, their chat automatically:
- Returns to the active list
- Gets the "New Message" badge
- Triggers a notification to the assigned manager or admin
