import { ClinicDetailView } from "@/components/clinic-detail-view";

interface ClinicDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function ClinicDetailPage({ params }: ClinicDetailPageProps) {
  const { id } = await params;
  return <ClinicDetailView clinicId={id} />;
}
