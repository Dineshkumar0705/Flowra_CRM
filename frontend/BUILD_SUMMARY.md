# Flowra CRM Frontend - Build Summary

## Project Overview
Complete Next.js 16 + React 19 + Tailwind CSS v4 + TypeScript frontend for Flowra CRM.

## Backend API Base URL
- `http://localhost:8000/api/v1`

## Files Created/Updated

### Configuration Files
- ✅ `package.json` - Updated with all required dependencies
- ✅ `tsconfig.json` - Already configured with @ path alias
- ✅ `next.config.ts` - React compiler enabled
- ✅ `postcss.config.mjs` - Tailwind configured

### Styling
- ✅ `src/app/globals.css` - Tailwind v4 with custom theme colors (indigo color scheme)

### App Structure

#### Root Layer
- ✅ `src/app/layout.tsx` - Root layout with providers and Toaster
- ✅ `src/app/page.tsx` - Redirect to /dashboard or /login

#### Auth Routes (`src/app/(auth)`)
- ✅ `src/app/(auth)/layout.tsx` - Split-screen auth layout (gradient + form)
- ✅ `src/app/(auth)/login/page.tsx` - Login page with email/password form
- ✅ `src/app/(auth)/signup/page.tsx` - Signup with name, email, password, workspace name

#### Dashboard Routes (`src/app/(dashboard)`)
- ✅ `src/app/(dashboard)/layout.tsx` - Main dashboard shell with sidebar + header
- ✅ `src/app/(dashboard)/dashboard/page.tsx` - Dashboard with stats, revenue chart, activity feed
- ✅ `src/app/(dashboard)/contacts/page.tsx` - Contacts list with search, filters, table
- ✅ `src/app/(dashboard)/deals/page.tsx` - Kanban board for deal pipeline management
- ✅ `src/app/(dashboard)/settings/page.tsx` - Settings (Profile, Security, Workspace, Notifications)

### Components

#### Layout Components (`src/components/layout`)
- ✅ `Sidebar.tsx` - Fixed left sidebar with navigation, user profile, logout
- ✅ `Header.tsx` - Top header with page title, notifications bell, user menu

#### UI Components (`src/components/ui`)
- ✅ `Button.tsx` - CVA-based button with variants (default, outline, ghost, destructive)
- ✅ `Input.tsx` - Styled input with label, error, helper text
- ✅ `Card.tsx` - Card, CardHeader, CardContent, CardFooter
- ✅ `Badge.tsx` - Colored badge (default, success, warning, danger, info)
- ✅ `Spinner.tsx` - Loading spinner animation
- ✅ `Modal.tsx` - Dialog wrapper using @radix-ui/react-dialog
- ✅ `Avatar.tsx` - Avatar with fallback initials using @radix-ui/react-avatar
- ✅ `Select.tsx` - Styled select dropdown

#### Dashboard Components (`src/components/dashboard`)
- ✅ `StatsCards.tsx` - 4 stat cards (Total Contacts, Active Deals, Revenue, Win Rate)
- ✅ `RevenueChart.tsx` - Line chart using Recharts for monthly revenue trend
- ✅ `ActivityFeed.tsx` - Recent notifications/activity list

#### Contacts Components (`src/components/contacts`)
- ✅ `ContactsTable.tsx` - Full contacts table with columns: name, company, email, phone, lead score, source, tags, actions
- ✅ `ContactDrawer.tsx` - Slide-over drawer to create/edit contacts

#### Deals Components (`src/components/deals`)
- ✅ `DealCard.tsx` - Draggable deal card using @dnd-kit/sortable
- ✅ `DealDrawer.tsx` - Slide-over drawer to create/edit deals
- ✅ `KanbanBoard.tsx` - Full Kanban board with @dnd-kit, drag-to-move functionality

#### Providers
- ✅ `src/components/providers.tsx` - QueryClientProvider wrapper

### Services (`src/services`)
- ✅ `apiClient.ts` - Axios instance with request/response interceptors for auth token management and refresh
- ✅ `authService.ts` - login, signup, refreshToken, getMe, changePassword
- ✅ `contactService.ts` - getContacts, createContact, getContact, updateContact, deleteContact, rescoreContact
- ✅ `dealService.ts` - getDeals, createDeal, getDeal, updateDeal, deleteDeal, moveDealStage, getDashboard
- ✅ `pipelineService.ts` - getPipelines, createPipeline, getPipelineBoard

### Hooks (`src/hooks`)
- ✅ `useAuth.ts` - Authentication hook (login, signup, logout, changePassword)
- ✅ `useApi.ts` - Generic API query/mutation hooks
- ✅ `useDeals.ts` - useDeals, useDealDashboard hooks
- ✅ `usePipeline.ts` - usePipelines, usePipelineBoard hooks

### Store (`src/store`)
- ✅ `authStore.ts` - Zustand auth store with persistence to localStorage

### Types (`src/types`)
- ✅ `index.ts` - All TypeScript interfaces: User, Workspace, Contact, Deal, Pipeline, Stage, Notification, etc.

### Utilities (`src/utils`)
- ✅ `cn.ts` - Class name utility (clsx + tailwind-merge)
- ✅ `format.ts` - Currency, date, number formatting with Indian locale (en-IN)
- ✅ `constants.ts` - API URL, contact sources, deal priorities, colors, etc.
- ✅ `helpers.ts` - Error messages, debounce, sleep utilities

## Design System

### Colors
- Primary: `#6366f1` (Indigo-500)
- Primary Dark: `#4f46e5` (Indigo-600)
- Sidebar: `#1e1b4b` (Deep Indigo)
- Sidebar Text: `#c7d2fe` (Indigo-200)

### Typography
- Font: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI, etc.)
- Spacing: Tailwind default

### Styling Features
- Tailwind CSS v4 with custom theme variables
- CVA for component variants
- Dark mode ready (structure in place)
- Smooth transitions on all interactive elements
- Custom scrollbar styling

## Features Implemented

### Authentication
- ✅ Login with email/password
- ✅ Signup with workspace creation
- ✅ Token refresh mechanism
- ✅ Protected routes with auto-redirect
- ✅ Persistent auth state (localStorage)

### Contacts Management
- ✅ List contacts with pagination
- ✅ Search and filter by source/tags
- ✅ Create/edit/delete contacts
- ✅ Lead score with rescore functionality
- ✅ Contact drawer form with validation

### Deals Management
- ✅ Kanban board for pipeline management
- ✅ Drag-and-drop to move deals between stages
- ✅ Pipeline selector dropdown
- ✅ Deal card with priority badge, value, contact name, date
- ✅ Create/edit deals with drawer form
- ✅ Multi-select pipeline stages

### Dashboard
- ✅ 4 stat cards (contacts, deals, revenue, win rate)
- ✅ Monthly revenue trend chart
- ✅ Recent activity feed
- ✅ Responsive grid layout

### Settings
- ✅ Profile tab (name, email, avatar)
- ✅ Security tab (change password)
- ✅ Workspace tab (workspace name, plan, members list)
- ✅ Notifications preferences

### UI/UX Features
- ✅ Loading spinners
- ✅ Toast notifications (Sonner)
- ✅ Form validation with error messages
- ✅ Responsive layout
- ✅ Hover states and transitions
- ✅ Pagination controls
- ✅ Dropdown menus
- ✅ Side drawer overlays

## Technical Details

### Dependencies Added
- `@dnd-kit/core` - Drag and drop
- `@dnd-kit/sortable` - Sortable drag and drop
- `@dnd-kit/utilities` - DnD utilities
- `recharts` - Charts library
- `class-variance-authority` - CVA for components
- `tailwind-merge` - Tailwind class merging
- `sonner` - Toast notifications
- `@radix-ui/*` - UI primitives (Dialog, Avatar, Select, Dropdown, etc.)

### Query Management
- TanStack React Query for server state management
- Automatic request deduplication and caching
- 5-minute stale time, 10-minute cache

### Form Handling
- Native HTML form validation
- Custom error state management
- Field-level error display

### State Management
- Zustand for auth state
- React Query for server state
- Local state for form/UI state

## Build & Run

```bash
# Install dependencies
npm install --legacy-peer-deps

# Development
npm run dev

# Production build
npm run build
npm start

# Lint
npm run lint
```

The frontend will be available at `http://localhost:3000`

## Backend Requirements

Ensure backend is running at `http://localhost:8000` with the following endpoints:

### Auth
- POST /auth/signup
- POST /auth/login
- POST /auth/refresh
- GET /auth/me
- POST /auth/change-password

### Contacts
- GET /contacts
- POST /contacts
- GET /contacts/:id
- PATCH /contacts/:id
- DELETE /contacts/:id
- POST /contacts/:id/rescore

### Deals
- GET /deals
- POST /deals
- GET /deals/dashboard
- PATCH /deals/:id
- DELETE /deals/:id
- POST /deals/:id/move-stage

### Pipelines
- GET /pipelines
- POST /pipelines
- GET /pipelines/:id/board

### Analytics
- GET /analytics/dashboard

### Notifications
- GET /notifications
- GET /notifications/unread-count
- POST /notifications/mark-all-read

### Workspace
- GET /workspaces/current
- PATCH /workspaces/current
- GET /workspaces/current/members

## Notes

- All API responses follow the standard envelope format: `{ success, data, message, meta }`
- Currency is formatted as Indian Rupees (₹) with Indian number formatting
- Dates are formatted as "DD MMM YYYY"
- All timestamps use dayjs for parsing and formatting
- The app uses "use client" directive only where necessary (hooks, interactions)
- Server components are used for data fetching where possible
- Error handling includes user-friendly toast messages
- Loading states are shown throughout the app
