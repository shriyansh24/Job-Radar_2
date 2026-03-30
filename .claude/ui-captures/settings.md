# Settings

## Route
- Path: `/settings`
- File: `src/pages/Settings.tsx`

## Figma Status: IN_FIGMA

## Layout Structure
- Container (space-y-6, px-4 py-4 sm:px-6 lg:px-8)
  - Custom hero panel (BRUTAL_PANEL_ALT)
    - Left: "Operations / Settings" eyebrow + "Settings console" h1 + description
    - Right: Signed in panel + Connected integrations panel
  - PageHeader (system, BRUTAL_PANEL override): "Settings" title + Export/Save buttons
  - MetricStrip (system, BRUTAL override): Saved searches, Alerts on, Connected integrations, Signed in
  - SplitWorkspace:
    - Primary (space-y-6):
      - Workspace defaults SettingsSection: Theme/Notifications/Auto-apply selects
      - Integrations SettingsSection: 4 provider cards (OpenRouter, SerpAPI, TheirStack, Apify) with key inputs
      - Saved searches SettingsSection: search cards with toggle/edit/delete + "New search" button
      - Security and data SettingsSection: password change form + data management (export/clear/delete)
    - Secondary (space-y-4):
      - 3 StateBlocks (Operational note, Current owner, Destructive actions warning)
  - Modal: Saved search editor (name, filters JSON, alert toggle)

## Components Used
- System: `PageHeader`, `MetricStrip`, `SettingsSection`, `SplitWorkspace`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `Input`, `Modal`, `Select`, `Skeleton`, `Textarea`
- Icons: CheckCircle, Code, Database, DownloadSimple, Key, Lock, MagnifyingGlass, PencilSimple, Trash, WarningCircle

## Theme & Styling
- BRUTAL overrides: all !important styles forcing neo-brutalist look on system components
- BRUTAL_PANEL: !rounded-none !border-2 !bg-secondary !shadow-[4px_4px_0_0]
- BRUTAL_BUTTON: same with !bg-secondary !text-primary
- BRUTAL_PRIMARY_BUTTON: !bg-accent-primary !text-white
- BRUTAL_FIELD: !rounded-none !border-2 !bg-secondary, focus:!border-accent-primary !ring-0
- Danger button: !bg-accent-danger !text-white

## Data/Content Shape
- settingsApi: getSettings, updateSettings(AppSettings), listSearches, createSearch, updateSearch, deleteSearch, listIntegrations, upsertIntegration, deleteIntegration
- AppSettings: theme, notifications_enabled, auto_apply_enabled
- IntegrationStatus: provider (openrouter|serpapi|theirstack|apify), connected, status, masked_value
- SavedSearch: id, name, filters (JSON), alert_enabled, last_checked_at
- Password form: currentPassword, newPassword, confirmPassword

## Responsive Behavior
- Hero: lg:grid-cols side-by-side
- Workspace defaults: md:grid-cols-3
- Integration cards: flex-col lg:flex-row
- Security: lg:grid-cols-2
- SplitWorkspace handles responsive stacking

---

## Light Theme

### Colors
- Background: #FFFFFF
- Text Primary: #000000
- Text Secondary: #666666
- Border: #E5E5E5
- Card Background: #F8F8F8
- Secondary: #F0F0F0
- Accent Primary: #0066FF
- Accent Danger: #FF0000
- Accent Success: #00AA00

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 !text-#000000 hover:!bg-#E5E5E5
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#0066FF !text-#FFFFFF hover:!bg-#0052CC
- BRUTAL_FIELD: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !text-#000000 focus:!border-#0066FF !ring-0
- Danger button: !rounded-none !border-2 !border-#FF0000 !bg-#FF0000 !text-#FFFFFF hover:!bg-#CC0000
- SettingsSection header: text-#000000, border-b-2 border-#000000
- Integration card: border-2 border-#E5E5E5, bg-#FFFFFF
- StateBlock: border-2 border-#E5E5E5, bg-#F0F0F0, text-#666666
- Modal backdrop: bg-#000000/50
- Modal: border-2 border-#000000, bg-#FFFFFF, shadow-[4px_4px_0_0_#000000]

---

## Dark Theme

### Colors
- Background: #0A0A0A
- Text Primary: #FFFFFF
- Text Secondary: #AAAAAA
- Border: #333333
- Card Background: #1A1A1A
- Secondary: #252525
- Accent Primary: #3399FF
- Accent Danger: #FF3333
- Accent Success: #00DD00

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 !text-#FFFFFF hover:!bg-#333333
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#3399FF !text-#000000 hover:!bg-#2680CC
- BRUTAL_FIELD: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !text-#FFFFFF focus:!border-#3399FF !ring-0
- Danger button: !rounded-none !border-2 !border-#FF3333 !bg-#FF3333 !text-#FFFFFF hover:!bg-#CC2222
- SettingsSection header: text-#FFFFFF, border-b-2 border-#FFFFFF
- Integration card: border-2 border-#333333, bg-#1A1A1A
- StateBlock: border-2 border-#333333, bg-#252525, text-#AAAAAA
- Modal backdrop: bg-#FFFFFF/10
- Modal: border-2 border-#FFFFFF, bg-#1A1A1A, shadow-[4px_4px_0_0_#FFFFFF]
