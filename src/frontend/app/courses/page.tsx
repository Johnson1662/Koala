import Link from "next/link";

export default function CoursesPage() {
  return (
    <main className="min-h-screen bg-[#FBF7F0] px-4 py-10">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[#3D2B1F]">我的课程</h1>
            <p className="text-[#8B6347] text-sm mt-1">选择已有课程，或创建新课程</p>
          </div>
          <Link href="/" className="text-[#5C8A3C] hover:underline text-sm">← 返回首页</Link>
        </div>

        <div className="bg-white rounded-2xl border border-[#E8F5E2] p-8 flex flex-col items-center justify-center text-center mb-6">
          <span className="text-5xl mb-4">📚</span>
          <p className="text-[#8B6347] text-base mb-6">还没有课程，上传你的学习材料开始吧！</p>
          <button
            className="bg-[#5C8A3C] hover:bg-[#4a7031] text-white font-semibold py-3 px-8 rounded-xl transition-colors"
            disabled
          >
            🌿 创建新课程（即将开放）
          </button>
        </div>

        <p className="text-center text-xs text-[#8B6347]">
          支持上传 PDF 或粘贴网页链接，Koala 将为你生成专属知识库
        </p>
      </div>
    </main>
  );
}
