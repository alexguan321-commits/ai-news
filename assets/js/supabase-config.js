// Supabase 配置
// ═══════════════════════════════════════════════════════════════
// 安全架构说明：
// anon key 故意公开（Supabase 设计如此），安全性完全依赖 RLS 策略：
//   - likes:       anon 只读，INSERT/UPDATE/DELETE 需认证且仅限本人数据
//   - comments:    anon 只读，INSERT/UPDATE/DELETE 需认证且仅限本人数据
//   - suggestions: anon 只读，INSERT/UPDATE/DELETE 需认证且仅限本人数据
//   - page_views:  anon 可 INSERT（设计如此，匿名访问统计）
// 审计日期: 2026-07-10
// ═══════════════════════════════════════════════════════════════
const SUPABASE_URL = 'https://xhmzbrvzuxbdcvntwlut.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhobXpicnZ6dXhiZGN2bnR3bHV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMxMjcwNjQsImV4cCI6MjA5ODcwMzA2NH0.sjMGP10WuIS5xPNul8uyq5LSB3JEEI6SDxqtDq7tPA8';

// 初始化函数 - 使用 Supabase 默认 session 管理
window.initSupabaseClient = function() {
  if (typeof window.supabase !== 'undefined' && !window.supabaseClient) {
    window.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true
      }
    });
    return true;
  }
  return !!window.supabaseClient;
};

// 立即尝试初始化
if (!window.initSupabaseClient()) {
  // 如果 Supabase 库还没加载，等待 DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function() {
    if (!window.initSupabaseClient()) {
      console.error('Supabase library failed to load');
    }
  });
}
