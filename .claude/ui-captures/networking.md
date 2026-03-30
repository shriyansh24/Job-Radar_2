# Networking

## Route
- Path: `/networking`
- File: `src/pages/Networking.tsx`

## Figma Status
MISSING_FROM_FIGMA

## Layout Structure
- Custom hero section (PANEL class, no system PageHeader):
  - Left: "Execute / Networking" eyebrow + "Networking" h1 + description
  - Right: 3 MetricCard tiles (Contacts, Avg strength, Referral queue)
- Two-column grid (xl:grid-cols-[0.95fr_1.05fr]):
  - Left: Contacts list (PANEL, scrollable max-h-[72vh])
    - Header: title + "New" button + search Input
    - ContactRow cards (selectable, shadow, hover translate)
  - Right (space-y-6):
    - Contact detail/edit form (PANEL): name, relationship, company, role, email, LinkedIn, notes + save/reset buttons
    - Two sub-panels (xl:grid-cols-2):
      - Company connection scan: company search + results
      - Referral desk: job select + suggest referrals + SuggestionCard list + outreach Textarea
    - Referral request queue (PANEL): list of draft requests

## Components Used
- UI: `Badge`, `Button`, `EmptyState`, `Input`, `Select`, `Skeleton`, `Textarea`
- Local: MetricCard, SectionTitle, ContactRow, SuggestionCard
- Icons: Buildings, ChatsCircle, Handshake, LinkSimple, MagnifyingGlass, NotePencil, PaperPlaneTilt, Plus, Trash, UserCircle, UsersThree

## Data/Content Shape
- networkingApi: listContacts, createContact, updateContact, deleteContact, findConnections, suggestReferrals, generateOutreach, listReferralRequests, createReferralRequest
- Contact: name, company, role, relationship_strength (1-5), linkedin_url, email, notes, last_contacted
- ReferralSuggestion: contact, relevance_reason, suggested_message
- ReferralRequest: contact_id, job_id, message_template, status

## Theme Variants
### Light Theme
- Hero: bg-secondary with text-primary
- Metric cards: bg-secondary border-2
- Panels (PANEL): border-2 bg-secondary shadow-[4px_4px_0_0]
- Selected contact: bg-accent-primary-subtle shadow with accent-primary border
- Contact hover: translate(-2px, -2px) with subtle shadow increase
- Forms: Input bg-primary border-primary focus:border-accent-primary
- Buttons: Primary (accent-primary), Secondary (border-2 text-primary)

### Dark Theme
- Hero: bg-secondary (darker) with text-primary (lighter)
- Metric cards: bg-secondary (darker) border-2
- Panels (PANEL): border-2 bg-secondary (darker) shadow-[4px_4px_0_0]
- Selected contact: bg-accent-primary-subtle (adjusted) shadow with accent-primary border
- Contact hover: translate(-2px, -2px) with subtle shadow increase
- Forms: Input bg-primary (darker) border-primary focus:border-accent-primary
- Buttons: Primary (accent-primary), Secondary (border-2 text-primary lighter)
