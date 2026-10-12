import type { LucideIcon } from "lucide-react";

type Props = {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
};

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: Props) {
  return (
    <div className="rounded-card border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-midnight">
            {value}
          </p>
        </div>

        <div className="rounded-xl bg-slate-100 p-3 text-slate-700">
          <Icon size={20} />
        </div>
      </div>

      <p className="mt-4 text-xs text-slate-500">{subtitle}</p>
    </div>
  );
}
