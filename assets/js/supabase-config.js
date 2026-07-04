// Supabase 配置
const SUPABASE_URL = 'https://xhmzbrvzuxbdcvntwlut.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhobXpicnZ6dXhiZGN2bnR3bHV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMxMjcwNjQsImV4cCI6MjA5ODcwMzA2NH0.sjMGP10WuIS5xPNul8uyq5LSB3JEEI6SDxqtDq7tPA8';

// 等待 Supabase 库加载完成后初始化 Client
function initSupabaseClient() {
  if (typeof window.supabase !== 'undefined') {
    window.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    return true;
  }
  return false;
}

// 立即尝试初始化
if (!initSupabaseClient()) {
  // 如果 Supabase 库还没加载，等待 DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function() {
    if (!initSupabaseClient()) {
      console.error('Supabase library failed to load');
    }
  });
}
