import Link from "next/link";
import KoalaLoader from "@/components/koala/KoalaLoader";

export default async function CourseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <main className="min-h-screen bg-[#FBF7F0] px-4 py-10">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link href="/courses" className="text-[#5C8A3C] hover:underline text-sm">← 返回课程列表</Link>
        </div>

        <div className="bg-white rounded-2xl border border-[#E8F5E2] p-10 flex flex-col items-center justify-center text-center">
          <KoalaLoader />
          <p className="text-[#8B6347] text-sm mt-4">课程详情加载中…</p>
          <p className="text-[#8B6347] text-xs mt-1 opacity-60">课程 ID：{(await params).id}</p>
        </div>
      </div>
    </main>
  );
}
