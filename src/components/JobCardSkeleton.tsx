export default function JobCardSkeleton() {
  return (
    <div className="bg-card-bg border border-border rounded-2xl p-5">
      <div className="animate-shimmer h-5 w-3/4 rounded-lg mb-2" />
      <div className="animate-shimmer h-4 w-1/3 rounded-lg mb-3" />
      <div className="flex gap-2 mb-3">
        <div className="animate-shimmer h-6 w-20 rounded-lg" />
        <div className="animate-shimmer h-6 w-16 rounded-lg" />
      </div>
      <div className="flex gap-3">
        <div className="animate-shimmer h-4 w-28 rounded-lg" />
        <div className="animate-shimmer h-4 w-24 rounded-lg" />
        <div className="animate-shimmer h-4 w-16 rounded-lg" />
      </div>
      <div className="mt-3 pt-3 border-t border-border flex gap-1">
        <div className="animate-shimmer h-5 w-14 rounded-md" />
        <div className="animate-shimmer h-5 w-12 rounded-md" />
        <div className="animate-shimmer h-5 w-16 rounded-md" />
      </div>
    </div>
  );
}
