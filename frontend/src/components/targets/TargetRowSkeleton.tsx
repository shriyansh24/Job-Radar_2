import Skeleton from "../ui/Skeleton";

export function TargetRowSkeleton() {
  return (
    <div className="grid gap-3 border-b-2 border-border px-5 py-4 md:grid-cols-[minmax(0,1.5fr)_140px_140px_150px]">
      <div className="space-y-2">
        <Skeleton variant="text" className="h-4 w-1/3" />
        <Skeleton variant="text" className="h-3 w-2/3" />
      </div>
      <Skeleton variant="text" className="h-4 w-16" />
      <Skeleton variant="text" className="h-4 w-16" />
      <Skeleton variant="text" className="h-4 w-12" />
    </div>
  );
}
