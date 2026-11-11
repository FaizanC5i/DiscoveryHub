import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

/** Loading state for the dashboard route. Mirrors the real layout to avoid layout shift. */
export function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-10" role="status" aria-label="Loading dashboard">
      <div className="flex flex-col gap-3">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-5 w-96 max-w-full" />
      </div>

      <div className="flex flex-col gap-4">
        <Skeleton className="h-5 w-40" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[0, 1].map((index) => (
            <Card key={index} className="flex flex-col gap-5 p-6">
              <Skeleton className="size-10" />
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-1.5 w-full" />
            </Card>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <Skeleton className="h-5 w-32" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[0, 1].map((index) => (
            <Card key={index} className="flex items-center gap-4 p-5">
              <Skeleton className="size-10 shrink-0" />
              <div className="flex flex-1 flex-col gap-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
