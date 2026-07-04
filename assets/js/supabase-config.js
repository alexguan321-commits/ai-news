// Supabase 配置
const SUPABASE_URL = 'https://xhmzbrvzuxbdcvntwlut.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhobXpicnZ6dXhiZGN2bnR3bHV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMxMjcwNjQsImV4cCI6MjA5ODcwMzA2NH0.sjMGP10WuIS5xPNul8uyq5LSB3JEEI6SDxqtDq7tPA8';

// 初始化 Supabase Client
const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
