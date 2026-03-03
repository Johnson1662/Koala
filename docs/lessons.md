# Koala 项目经验教训

**目的**：记录开发过程中遇到的错误和教训，每次会话开始时回顾最近 3–5 条，避免重复犯错。

---

## 格式规范

```
### [日期] 教训标题
**场景**：什么情况下发生的
**错误**：做了什么错误的事
**根因**：为什么会犯这个错
**正确做法**：以后应该怎么做
**影响文件/规则**：是否需要更新 CLAUDE.md
```

---

## 教训记录

### 2026-03-03 tasks/ 目录路径不一致
**场景**：制定实施计划，创建 `tasks/` 目录存放 `todo.md` 和 `lessons.md`  
**错误**：CLAUDE.md 关键文档索引表格中把 `lessons.md` 路径写成了 `docs/lessons.md`，而工作流章节写的是 `tasks/lessons.md`，产生不一致  
**根因**：文档跨章节编写时未做全局一致性检查  
**正确做法**：文档中涉及路径的地方，写完后全文搜索该路径确认一致；本次统一改为 `docs/` 目录  
**影响**：已更新 CLAUDE.md，所有路径统一为 `docs/todo.md` 和 `docs/lessons.md`，`tasks/` 目录已删除

---

### 2026-03-03 Node.js 24 + Next.js 14 + Tailwind CSS v3 兼容性问题
**场景**：Phase 0 前端脚手架，运行 `npm run build` 时构建失败  
**错误**：`globals.css` 被 sucrase（JS 解析器）错误处理，触发 SyntaxError（`@tailwind` 指令被当成 JS 解析）  
**根因**：tailwindcss v3 内置的 `postcss-load-config` 在 Node.js 24 下行为异常，导致 sucrase 参与了 CSS 文件的处理链  
**正确做法**：
1. 升级 Next.js 14 → **15**（官方支持 Node.js 24）
2. 升级 Tailwind CSS v3 → **v4**，配套安装 `@tailwindcss/postcss`
3. `postcss.config.js` 改用 `"@tailwindcss/postcss": {}` 替代 `tailwindcss: {}`
4. `globals.css` 改用 `@import "tailwindcss"` + `@theme {}` 块替代 `@tailwind base/components/utilities`
5. 删除 `tailwind.config.ts`（v4 不再需要）  
**影响文件**：`postcss.config.js`、`globals.css`、`package.json`、删除 `tailwind.config.ts`

_（后续教训追加在此）_
