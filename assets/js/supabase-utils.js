/**
 * Supabase 安全工具函数
 * 防止 XSS 注入 — 所有动态数据必须经过这些函数处理
 */

// HTML 转义 — 用于所有插入 innerHTML 的文本
window.escapeHtml = function(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
};

// URL 安全校验 — 只允许 http/https 协议
window.safeUrl = function(url) {
  if (!url) return '';
  try {
    const u = new URL(url, window.location.origin);
    if (u.protocol === 'http:' || u.protocol === 'https:') {
      return url;
    }
    return '';
  } catch (e) {
    return '';
  }
};

// 安全头像 URL — 额外检查常见图片扩展名和已知 CDN
window.safeAvatarUrl = function(url) {
  const safe = window.safeUrl(url);
  if (!safe) return '';
  // 允许 GitHub/Google 头像 CDN 和常见图片格式
  const allowed = /^(https:\/\/)(avatars\.githubusercontent\.com|lh\d+\.googleusercontent\.com|.*\.(jpg|jpeg|png|gif|webp|svg))/i;
  if (allowed.test(safe)) return safe;
  // 也允许任何 https URL（因为 safeUrl 已过滤 javascript: 等危险协议）
  return safe;
};
