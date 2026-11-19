import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

/** Shown while the project loads. Mirrors the summary card so the page does not jump. */
export default function ProjectOverviewLoading() {
  return (
    <div className="flex flex-col gap-6" role="status" aria-label="Loading project">
      <Card className="flex flex-col gap-6 p-8">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-8 w-80 max-w-full" />
          <Skeleton className="h-5 w-96 max-w-full" />
        </div>
        <div className="grid grid-cols-2 gap-4 border-t border-border-subtle pt-4 sm:grid-cols-5">
          {[0, 1, 2, 3, 4].map((index) => (
            <div key={index} className="flex flex-col gap-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-5 w-24" />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
