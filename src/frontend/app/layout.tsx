import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Koala - 你的 AI 学习伙伴",
  description: "沉浸式多模态 AI 学习助手，基于 Google ADK + Gemini",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className="bg-[#FBF7F0] text-[#3D2B1F] antialiased min-h-screen"
      >
        {children}
      </body>
    </html>
  );
}
