import Link from "next/link";
import KoalaLoader from "@/components/koala/KoalaLoader";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#FBF7F0] flex flex-col items-center px-4 py-12">
      {/* 顶部标题 */}
      <section className="text-center mb-12">
        <div className="mb-4 flex justify-center">
          <span className="text-6xl">🐨</span>
        </div>
        <h1 className="text-4xl font-bold text-[#5C8A3C] mb-2">Koala</h1>
        <p className="text-[#8B6347] text-lg">你的沉浸式 AI 学习伙伴</p>
      </section>

      {/* XP 卡片 */}
      <section className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-[#E8F5E2] p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#8B6347] mb-1">今日 XP</p>
            <p className="text-3xl font-bold text-[#5C8A3C]">0</p>
          </div>
          <div className="text-4xl">⭐</div>
        </div>
        <div className="mt-4 h-2 bg-[#E8F5E2] rounded-full">
          <div className="h-2 bg-[#5C8A3C] rounded-full w-0" />
        </div>
        <p className="text-xs text-[#8B6347] mt-2">继续学习获得更多 XP！</p>
      </section>

      {/* 进行中的课程（占位） */}
      <section className="w-full max-w-md mb-8">
        <h2 className="text-lg font-semibold text-[#3D2B1F] mb-3">进行中的课程</h2>
        <div className="bg-white rounded-2xl shadow-sm border border-[#E8F5E2] p-8 flex flex-col items-center justify-center text-center">
          <KoalaLoader />
          <p className="text-[#8B6347] text-sm mt-4">还没有课程，快去创建一个吧！</p>
        </div>
      </section>

      {/* 新建课程按钮 */}
      <Link
        href="/courses"
        className="w-full max-w-md bg-[#5C8A3C] hover:bg-[#4a7031] text-white font-semibold py-4 px-8 rounded-2xl text-center transition-colors block text-lg shadow-md"
      >
        🌿 开始新课程
      </Link>
    </main>
  );
}
