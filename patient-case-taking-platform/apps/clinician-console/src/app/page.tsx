import { StatCard } from "@/components/StatCard";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-primary">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active Encounters" value={0} />
        <StatCard title="Pending Reviews" value={0} />
        <StatCard title="Alerts" value={0} />
        <StatCard title="Patients Today" value={0} />
      </div>

      <section className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-semibold text-primary mb-4">Recent Encounters</h2>
        <p className="text-gray-500 text-sm">No encounters yet.</p>
      </section>
    </div>
  );
}
