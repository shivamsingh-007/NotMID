import Link from "next/link";
import { buttonClassName } from "@/components/Button";

export default function RecordsPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="text-3xl font-bold text-primary">Patient records view</h1>
      <p className="text-gray-600">रोगी रिकॉर्ड देखें</p>
      <Link href="/" className={buttonClassName("secondary")}>
        Back / वापस
      </Link>
    </main>
  );
}
