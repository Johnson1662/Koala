import Link from "next/link";
import KoalaLoader from "@/components/koala/KoalaLoader";

export default async function LessonPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <main className="min-h-screen bg-[#FBF7F0] flex flex-col">
      <header className="bg-white border-b border-[#E8F5E2] px-4 py-3 flex items-center justify-between">
        <Link href="/courses" className="text-[#5C8A3C] hover:underline text-sm">← 退出关卡</Link>
        <div className="flex items-center gap-2">
          <span className="text-sm text-[#8B6347]">XP</span>
          <span className="font-bold text-[#5C8A3C]">0</span>
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center px-4 py-10">
        <div className="w-full max-w-xl bg-white rounded-2xl border border-[#E8F5E2] p-10 flex flex-col items-center text-center">
          <KoalaLoader />
          <p className="text-[#8B6347] text-sm mt-4">关卡内容加载中…</p>
          <p className="text-[#8B6347] text-xs mt-1 opacity-60">关卡 ID：{(await params).id}</p>
        </div>
      </div>

      <footer className="bg-white border-t border-[#E8F5E2] px-4 py-3 flex items-center justify-center">
        <p className="text-xs text-[#8B6347]">🐨 Koala 正陪你学习</p>
      </footer>
    </main>
  );
}
