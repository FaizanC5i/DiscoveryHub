# Next.js 16.4.5 Prerendering Warnings - Fixed

## Problem

Next.js 16.4.5 introduced a new "instant navigation" feature that tries to render pages without waiting for data. This caused warnings when routes fetched real-time data with `cache: "no-store"`:

```
Error: Route "/dashboard": Next.js encountered uncached data during prerendering or a navigation.

`fetch(...)` accessed outside of `<Suspense>` prevents the route from being prerendered 
or the navigation from being instant, leading to a slower user experience.
```

**Affected routes:**
- `/dashboard` - fetches current user and dashboard data
- `/projects/[projectId]/overview` - fetches project data
- `/(app)/layout.tsx` - fetches current user in all authenticated routes

## Root Cause

When pages call `apiRequest()` with `cache: "no-store"` (which is required for auth state), Next.js assumes the data can be cached. However, the page doesn't have a cache, so Next.js warns about "uncached data".

Next.js 16.4.5's instant navigation tries to prefetch/render pages immediately, but this conflicts with routes that must fetch live data on every request.

## Solution

Added `export const instant = false` to all routes that require real-time data. This tells Next.js:

> "This route must wait for live data; don't attempt instant navigation."

### Files Changed

1. **`app/(app)/layout.tsx`** - Added to app shell (wraps all authenticated routes)
2. **`app/(app)/(main)/dashboard/page.tsx`** - Fetches user + dashboard data
3. **`app/(app)/(project)/projects/[projectId]/layout.tsx`** - Fetches project data
4. **`app/(app)/(project)/projects/[projectId]/overview/page.tsx`** - Displays project details

### Code Change Pattern

```typescript
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard",
};

// ✅ Tell Next.js this route needs blocking data fetches
export const instant = false;

export default async function DashboardPage() {
  // Fetch live data here
}
```

## Why This Works

- `export const instant = false` is an explicit signal that the route is dynamic/blocking
- Next.js respects this and doesn't attempt instant navigation
- The underlying issue (cache: "no-store" for auth state) remains correct
- `<Suspense>` boundaries still show loading states while data is fetched
- No performance regression; auth state must always be fresh anyway

## Verification

Run the dev server and check the console for prerendering warnings:

```bash
cd frontend
npm run dev
```

Navigate to:
- `http://localhost:3001/dashboard`
- `http://localhost:3001/projects/1/overview`

**Before fix:** Console shows "encountered uncached data" errors
**After fix:** No warnings; pages render correctly with loading skeletons

## Additional Context

- `cache: "no-store"` is necessary because auth tokens expire (15m access token)
- Tokens are sent via HttpOnly cookies, so server must forward them
- `React.cache()` deduplicates requests within a single render
- `<Suspense>` boundaries show loading UI while data arrives
- `instant = false` prevents the new instant-navigation feature from interfering

## References

- [Next.js 16 Instant Navigation](https://nextjs.org/docs/messages/blocking-prerender-dynamic)
- [Dynamic Data Fetching](https://nextjs.org/docs/app/building-your-application/data-fetching/fetching-caching-and-revalidating)

---

**Fixed:** 2026-11-11
**Next.js Version:** 16.4.5
