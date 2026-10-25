import { Skeleton } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div aria-busy="true">
      <Skeleton width={180} height={14} />
      <Skeleton width="55%" height={36} style={{ marginTop: 14 }} />
      <Skeleton height={34} width="70%" style={{ marginTop: 22 }} />
      <Skeleton height={520} style={{ marginTop: 16 }} />
    </div>
  );
}
