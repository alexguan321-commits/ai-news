审查完成，让我直接在终端输出完整报告。以下是逐文件审查的结果：

---

# AI News Website - 端到端代码审查报告

**审查日期**: 2026-07-04
**审查范围**: 21 个核心源文件 + 74 个报告页面 + 31 个知识卡片页面

---

## 1. 执行摘要

项目整体架构清晰（静态站点生成 + Supabase BaaS），CSS 设计质量高（glassmorphism + 响应式完善），但存在 **2 个 P0 安全漏洞**（4 处 XSS 注入向量、Supabase Anon Key 硬编码暴露），**5 个 P1 问题**（点赞竞态条件、page_views 表缺失 RLS、Markdown 链接未做协议白名单、avatar_url 未校验、git add 过度提交）。最紧迫的是 XSS 注入 -- 评论渲染、用户 UI 更新、头像 URL 等 4 处将未转义的用户数据直接插入 `innerHTML`。

---

## 2. 严重问题（P0 -- 必须立即修复）

### P0-1: XSS 注入 -- 4 处未转义的用户数据插入 innerHTML

#### A. 评论渲染 -- 用户名未转义

**文件**: `assets/js/supabase-interactions.js:191-214` (`renderComment`)

```javascript
<span class="comment-author">${comment.profile?.display_name || 'Anonymous'}</span>
```

`display_name` 未转义直接插入 innerHTML。攻击者注册一个 `display_name` 为 `<img src=x onerror=alert(1)>` 的账号后，所有浏览该用户评论的人都会执行脚本。

**修复**: 用 `this.escapeHtml()` 包裹所有动态数据：
```javascript
<span class="comment-author">${this.escapeHtml(comment.profile?.display_name || 'Anonymous')}</span>
```

#### B. 用户菜单 -- display_name/email/avatar_url 未转义

**文件**: `assets/js/supabase-auth.js:146-151`

```javascript
${this.profile?.avatar_url 
  ? `<img src="${this.profile.avatar_url}" alt="avatar">`
<span class="user-name">${this.profile?.display_name || this.user.email?.split('@')[0] || 'User'}</span>
```

`avatar_url` 可注入 `javascript:` 协议或 `onerror` 事件，`display_name` 和 `email` 同样未转义。

**修复**:
```javascript
function esc(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}
function safeAvatarUrl(url) {
  if (!url) return '';
  try {
    const u = new URL(url, window.location.origin);
    return u.protocol.startsWith('http') ? url : '';
  } catch { return ''; }
}
```

#### C. Supabase Interactions 中 avatar_url 同理

**文件**: `assets/js/supabase-interactions.js:193-194`

```javascript
const avatar = comment.profile?.avatar_url 
  ? `<img src="${comment.profile.avatar_url}" alt="" class="comment-avatar">`
```

同样需要 URL 校验。

### P0-2: Supabase Anon Key 硬编码暴露

**文件**: `assets/js/supabase-config.js:2-3`

```javascript
const SUPABASE_URL = 'https://xhmzbrzuxbdcvntwlut.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
```

虽然 anon key 设计为可公开（配合 RLS），但 **RLS 策略不完善**（见 P1-2），攻击者可以直接向数据库写入垃圾数据或读取 profiles。

**修复**: 先修复 RLS（P1-2），再考虑 Edge Function 代理。

---

## 3. 重要问题（P1 -- 本周修复）

### P1-1: 点赞/收藏竞态条件

**文件**: `assets/js/supabase-interactions.js:81-125`

**问题**: 
- 前端状态和数据库可能不同步
- 快速双击触发并发请求，UNIQUE 约束会 reject 第二条 insert，但前端乐观更新显示错误状态
- 没有 `upsert` 或操作后重新同步数据库状态

**修复**: 操作后调用 `loadUserState()` 和 `loadStats()` 重新同步，并用 `disabled` 防止重复点击。

### P1-2: `page_views` 表缺失 RLS 策略

**文件**: `supabase/schema.sql`

`page_views` 在 `supabase-views.js` 中被大量使用，但 **schema.sql 中完全没有定义这个表和 RLS**。

**修复**: 补充表定义和 RLS：
```sql
CREATE TABLE public.page_views (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  content_type TEXT NOT NULL,
  content_id TEXT NOT NULL,
  user_id UUID REFERENCES public.profiles(id),
  visitor_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.page_views ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can insert page views" ON public.page_views FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can read page view counts" ON public.page_views FOR SELECT USING (true);
```

### P1-3: Markdown 链接未做协议白名单

**文件**: `generate_index.py:451, 465, 480, 483`

```python
text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
```

如果内容包含 `[click](javascript:alert(1))`，会直接生成可执行的链接。

**修复**:
```python
def safe_link(match):
    url = match.group(2)
    if url.startswith(('http://', 'https://', '/')):
        return f'<a href="{match.group(2)}">{match.group(1)}</a>'
    return match.group(0)
```

### P1-4: `avatar_url` 未做 URL 校验

**文件**: `assets/js/supabase-auth.js:147` 和 `supabase-interactions.js:193-194`

如果 `avatar_url` 是 `javascript:alert(1)` 或 `data:text/html,...`，在某些浏览器中会被执行。

### P1-5: `publish_to_website.py` 中 `git add .` 过度提交

**文件**: `publish_to_website.py:160`

```python
subprocess.run(["git", "add", "."], check=True)
```

一旦 `.gitignore` 变化就可能泄露敏感文件。

---

## 4. 改进建议（P2 -- 有空再改）

| # | 问题 | 文件 | 说明 |
|---|------|------|------|
| P2-1 | 搜索性能差 | `index.html:876-921` | DOM 遍历搜索，1000+ 记录会卡顿。建议预存 JS 数组 + 虚拟滚动 |
| P2-2 | 两套 Markdown 渲染引擎 | `generate_index.py` vs `build_static_site.py` | 一套自研、一套用 `markdown` 库，输出不一致 |
| P2-3 | `_site/` 构建产物混入 | `publish_to_website.py` | 复制 `_site/` 内容到根目录，可能被 git add |
| P2-4 | CDN 版本号硬编码 | 多处 `?v=20260704` | 更新需手动改多处 |
| P2-5 | 无 favicon/OG meta | `index.html` | 分享链接无预览图 |
| P2-6 | kc-summary 多处为空 | `index.html:550,563,590` | 视觉上出现空白行 |
| P2-7 | 双重部署 | `deploy.yml` + `pages.yml` | Vercel + GitHub Pages 同时触发 |
| P2-8 | visitor_id 可预测 | `supabase-views.js:16` | `Math.random()` 非加密安全，用 `crypto.getRandomValues()` |
| P2-9 | 本地路径硬编码 | `batch_publish.py:14-17` | `~/.hermes/cron/output/...` 其他用户无法运行 |
| P2-10 | 评论回复 maxlength 纯前端 | `supabase-interactions.js:210` | 可被绕过，数据库有 CHECK 保护 |
| P2-11 | 隐私过滤无法关闭 | `generate_index.py:143-145` | `should_filter_content()` 始终返回 True |
| P2-12 | 报告含本地路径链接 | 报告页面 | `~/AI_News/raw/...` 在浏览器中无效 |

---

## 5. 代码质量评分

| 维度 | 得分 | 说明 |
|------|------|------|
| **安全性** | 4/10 | 多处 XSS 向量、anon key 暴露、URL 无白名单 |
| **性能** | 7/10 | CSS 良好、搜索需优化、无资源压缩 |
| **可维护性** | 6/10 | 两套渲染引擎不一致、硬编码多处 |
| **响应式设计** | 9/10 | 多断点、touch、safe-area、reduced-motion 完善 |
| **数据完整性** | 6/10 | RLS 基本覆盖但 page_views 缺失、竞态条件 |
| **代码规范** | 7/10 | 命名一致，但混合 inline onclick 和事件监听 |
| **浏览器兼容** | 7/10 | `-webkit-` 前缀完善，Safari backdrop-filter 降级需关注 |
| **总体** | **6.6/10** | 设计优秀、功能完整，安全性是最大短板 |

---

## 6. 修复优先级

1. **今天**: 修复 P0-1 -- 4 处 XSS 注入，全部用 `escapeHtml()` / `safeAvatarUrl()` 包裹
2. **今天**: 修复 P1-3 -- Markdown 链接协议白名单
3. **本周**: 修复 P1-1 -- 点赞竞态条件 + 操作后同步数据库状态
4. **本周**: 修复 P1-2 -- page_views 表补充 RLS 策略
5. **下周**: 考虑 P0-2 -- Edge Function 代理 Supabase 调用
6. **有空**: 处理所有 P2 改进项
