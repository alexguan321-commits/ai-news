// Supabase 配置
const SUPABASE_URL = 'https://xhmzbrvzuxbdcvntwlut.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhobXpicnZ6dXhiZGN2bnR3bHV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMxMjcwNjQsImV4cCI6MjA5ODcwMzA2NH0.sjMGP10WuIS5xPNul8uyq5LSB3JEEI6SDxqtDq7tPA8';

// 初始化函数 - 配置 72 小时 session 过期
window.initSupabaseClient = function() {
  if (typeof window.supabase !== 'undefined' && !window.supabaseClient) {
    window.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        // 72 小时 = 259200 秒
        storageExpiresIn: 259200
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
