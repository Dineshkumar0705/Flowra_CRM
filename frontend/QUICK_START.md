# Flowra CRM Frontend - Quick Start Guide

## Installation

```bash
cd /sessions/nifty-nice-bell/mnt/flowra/frontend
npm install --legacy-peer-deps
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Key Files to Know

### Pages
- `src/app/(auth)/login/page.tsx` - Login page
- `src/app/(auth)/signup/page.tsx` - Signup page
- `src/app/(dashboard)/dashboard/page.tsx` - Main dashboard
- `src/app/(dashboard)/contacts/page.tsx` - Contacts list
- `src/app/(dashboard)/deals/page.tsx` - Deals kanban
- `src/app/(dashboard)/settings/page.tsx` - User settings

### Core Components
- `src/components/layout/Sidebar.tsx` - Navigation sidebar
- `src/components/layout/Header.tsx` - Top header bar
- `src/components/dashboard/StatsCards.tsx` - Dashboard stats
- `src/components/contacts/ContactsTable.tsx` - Contacts list
- `src/components/deals/KanbanBoard.tsx` - Kanban board

### Services
- `src/services/authService.ts` - Authentication API
- `src/services/contactService.ts` - Contacts API
- `src/services/dealService.ts` - Deals API
- `src/services/pipelineService.ts` - Pipelines API

### State & Hooks
- `src/store/authStore.ts` - Zustand auth state
- `src/hooks/useAuth.ts` - Authentication hook

## Backend Requirements

Ensure the backend is running at `http://localhost:8000` with endpoints:

**Required Endpoints:**
- POST `/api/v1/auth/signup` - Create account
- POST `/api/v1/auth/login` - Login
- POST `/api/v1/auth/refresh` - Refresh token
- GET `/api/v1/auth/me` - Get current user
- GET `/api/v1/contacts` - List contacts
- POST `/api/v1/contacts` - Create contact
- GET `/api/v1/deals` - List deals
- GET `/api/v1/pipelines` - List pipelines
- GET `/api/v1/pipelines/:id/board` - Get pipeline board

See `IMPLEMENTATION_COMPLETE.md` for full endpoint list.

## Environment

No `.env` file needed for local development. Backend URL is hardcoded to:
```
http://localhost:8000/api/v1
```

For production deployment, update `src/services/apiClient.ts`:
```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
```

## Project Structure

```
src/
├── app/                    # Pages and layouts
├── components/             # Reusable components
├── services/              # API calls
├── hooks/                 # Custom hooks
├── store/                 # State management (Zustand)
├── types/                 # TypeScript interfaces
└── utils/                 # Utilities
```

## Styling

- **Framework**: Tailwind CSS v4
- **Components**: CVA-based with variants
- **Colors**: Indigo color scheme (#6366f1 primary)
- **Utilities**: `src/utils/cn.ts` for class merging

## Forms

All forms include:
- ✅ Validation
- ✅ Error messages
- ✅ Loading states
- ✅ Toast notifications

## API Client

Auto-handles:
- ✅ Request/response interceptors
- ✅ Bearer token injection
- ✅ Token refresh on 401
- ✅ Error handling

See `src/services/apiClient.ts`

## Build Commands

```bash
# Development
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint
```

## Testing the App

1. **Create Account**: Signup at `/signup`
2. **Login**: Use email/password
3. **View Dashboard**: See stats and charts
4. **Manage Contacts**: Create, edit, search contacts
5. **Manage Deals**: Drag deals in kanban board
6. **Settings**: Update profile and password

## Troubleshooting

**Port 3000 already in use:**
```bash
npx kill-port 3000
npm run dev
```

**Backend connection error:**
- Ensure backend is running at `http://localhost:8000`
- Check API endpoint response format

**Styling not working:**
```bash
npm install
```

## Documentation

- `BUILD_SUMMARY.md` - Comprehensive build details
- `IMPLEMENTATION_COMPLETE.md` - Full feature list
- `FILE_MANIFEST.txt` - All files created

## Next Steps

1. Start the backend at `http://localhost:8000`
2. Run `npm install --legacy-peer-deps`
3. Run `npm run dev`
4. Navigate to `http://localhost:3000`
5. Create an account and explore!

---

**Happy coding!** 🚀
