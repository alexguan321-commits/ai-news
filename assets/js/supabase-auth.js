/**
 * Supabase Auth 模块
 * 处理用户登录、注册、OAuth
 */

class SupabaseAuth {
  constructor() {
    this.user = null;
    this.profile = null;
    this.listeners = [];
    
    // 等待 supabaseClient 就绪
    if (typeof window.supabaseClient !== 'undefined') {
      this.init();
    } else {
      document.addEventListener('DOMContentLoaded', () => {
        if (typeof window.supabaseClient !== 'undefined') {
          this.init();
        } else {
          console.error('supabaseClient not available');
        }
      });
    }
  }

  async init() {
    // 检查 3 天登录过期
    const SESSION_DURATION = 3 * 24 * 60 * 60; // 3 天 = 259200 秒
    const loginTime = localStorage.getItem('login_timestamp');
    if (loginTime) {
      const elapsed = Math.floor(Date.now() / 1000) - parseInt(loginTime);
      if (elapsed > SESSION_DURATION) {
        // 过期，自动登出
        localStorage.removeItem('login_timestamp');
        await supabaseClient.auth.signOut();
        this.updateUI();
        return;
      }
    }

    // 先注册 auth 状态变化监听器（确保能捕获 OAuth 回调）
    supabaseClient.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session) {
        this.user = session.user;
        // OAuth 登录也需要记录时间戳
        if (!localStorage.getItem('login_timestamp')) {
          localStorage.setItem('login_timestamp', Math.floor(Date.now() / 1000).toString());
        }
        await this.loadProfile();
      } else if (event === 'SIGNED_OUT') {
        this.user = null;
        this.profile = null;
        localStorage.removeItem('login_timestamp');
      }
      this.notifyListeners();
      this.updateUI();
    });

    // 等待一小段时间让 detectSessionInUrl 处理 OAuth 回调
    await new Promise(resolve => setTimeout(resolve, 100));

    // 获取当前 session
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (session) {
      this.user = session.user;
      await this.loadProfile();
    }

    // 更新 UI 并通知所有监听器（即使 session 已存在也要通知）
    this.notifyListeners();
    this.updateUI();
  }

  async loadProfile() {
    if (!this.user) return;
    const { data } = await supabaseClient
      .from('profiles')
      .select('*')
      .eq('id', this.user.id)
      .single();
    this.profile = data;
  }

  // OAuth 登录
  async signInWithOAuth(provider) {
    const { error } = await supabaseClient.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: window.location.href
      }
    });
    if (error) {
      console.error('OAuth error:', error);
      alert('登录失败: ' + error.message);
    }
  }

  // 邮箱登录
  async signInWithEmail(email, password) {
    const { error } = await supabaseClient.auth.signInWithPassword({
      email,
      password
    });
    if (error) {
      console.error('Sign in error:', error);
      alert('登录失败: ' + error.message);
      return false;
    }
    // 记录登录时间戳（用于 3 天过期检查）
    localStorage.setItem('login_timestamp', Math.floor(Date.now() / 1000).toString());
    return true;
  }

  // 邮箱注册
  async signUpWithEmail(email, password, displayName) {
    const { error } = await supabaseClient.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: displayName
        }
      }
    });
    if (error) {
      console.error('Sign up error:', error);
      alert('注册失败: ' + error.message);
      return false;
    }
    alert('注册成功！请检查邮箱验证。');
    return true;
  }

  // 登出
  async signOut() {
    const { error } = await supabaseClient.auth.signOut();
    if (error) {
      console.error('Sign out error:', error);
    }
  }

  // 检查是否登录
  isLoggedIn() {
    return this.user !== null;
  }

  // 检查是否管理员
  isAdmin() {
    return this.profile?.role === 'admin';
  }

  // 订阅变化
  onChange(callback) {
    this.listeners.push(callback);
  }

  notifyListeners() {
    this.listeners.forEach(cb => cb(this.user, this.profile));
  }

  // 更新 UI
  updateUI() {
    const authContainer = document.getElementById('auth-container');
    if (!authContainer) return;

    // 始终显示内容（公开访问）
    window.hideLoginGate();

    if (this.isLoggedIn()) {
      const safeAvatar = safeAvatarUrl(this.profile?.avatar_url);
      const safeName = escapeHtml(this.profile?.display_name || this.user.email?.split('@')[0] || 'User');
      const initialLetter = escapeHtml((this.profile?.display_name || this.user.email || '?')[0].toUpperCase());
      authContainer.innerHTML = `
        <div class="user-menu">
          <button class="user-avatar-btn" onclick="auth.toggleUserDropdown()">
            ${safeAvatar 
              ? `<img src="${safeAvatar}" alt="avatar">`
              : `<span class="avatar-placeholder">${initialLetter}</span>`
            }
            <span class="user-name">${safeName}</span>
          </button>
          <div class="user-dropdown" id="user-dropdown" style="display:none;">
            <a href="/ai-news/bookmarks/" class="dropdown-item">⭐ My Bookmarks</a>
            <a href="/ai-news/suggestions/" class="dropdown-item">💡 My Suggestions</a>
            ${this.isAdmin() ? '<a href="/ai-news/admin/" class="dropdown-item">🔧 Admin</a>' : ''}
            <hr>
            <button class="dropdown-item" onclick="auth.signOut()">Sign Out</button>
          </div>
        </div>
      `;
    } else {
      authContainer.innerHTML = `
        <button class="login-btn" onclick="auth.showLoginModal()">登录</button>
      `;
    }
  }

  toggleUserDropdown() {
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) {
      dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
  }

  showLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
      modal.style.display = 'flex';
    } else {
      this.createLoginModal();
    }
  }

  createLoginModal() {
    const modal = document.createElement('div');
    modal.id = 'login-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-content">
        <button class="modal-close" onclick="auth.closeLoginModal()">&times;</button>
        <h2>Sign In</h2>
        
        <div class="oauth-buttons">
          <button class="oauth-btn github" onclick="auth.signInWithOAuth('github')">
            <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
            Continue with GitHub
          </button>
          <button class="oauth-btn google" onclick="auth.signInWithOAuth('google')">
            <svg viewBox="0 0 24 24" width="20" height="20"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Continue with Google
          </button>
        </div>

        <div class="divider">
          <span>or use email</span>
        </div>

        <form id="email-login-form" onsubmit="auth.handleEmailLogin(event)">
          <input type="email" id="login-email" placeholder="Email" required>
          <input type="password" id="login-password" placeholder="Password" required>
          <button type="submit" class="submit-btn">Sign In</button>
        </form>

        <p class="switch-form">
          Don't have an account?<a href="#" onclick="auth.showSignupForm(); return false;">Sign Up</a>
        </p>
      </div>
    `;
    document.body.appendChild(modal);
  }

  closeLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) modal.remove();
  }

  async handleEmailLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const success = await this.signInWithEmail(email, password);
    if (success) this.closeLoginModal();
  }

  showSignupForm() {
    const modal = document.getElementById('login-modal');
    if (!modal) return;
    
    const content = modal.querySelector('.modal-content');
    content.innerHTML = `
      <button class="modal-close" onclick="auth.closeLoginModal()">&times;</button>
      <h2>Create Account</h2>
      
      <form id="signup-form" onsubmit="auth.handleSignup(event)">
        <input type="text" id="signup-name" placeholder="Display Name" required>
        <input type="email" id="signup-email" placeholder="Email" required>
        <input type="password" id="signup-password" placeholder="Password (min 6 chars)" minlength="6" required>
        <button type="submit" class="submit-btn">Sign Up</button>
      </form>

      <p class="switch-form">
        Already have an account?<a href="#" onclick="auth.showLoginForm(); return false;">Sign In</a>
      </p>
    `;
  }

  showLoginForm() {
    this.closeLoginModal();
    this.createLoginModal();
  }

  async handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const success = await this.signUpWithEmail(email, password, name);
    if (success) this.closeLoginModal();
  }
}

// 全局实例 - 等待 supabaseClient 就绪后创建
function createAuthInstance() {
  if (typeof window.supabaseClient !== 'undefined' && !window.auth) {
    window.auth = new SupabaseAuth();
    
    // 内容默认公开可见
    window.hideLoginGate();
    
    return true;
  }
  return false;
}

// 显示登录门控
window.showLoginGate = function() {
  // 显示全屏登录页
  let loginGate = document.getElementById('login-gate');
  if (!loginGate) {
    loginGate = document.createElement('div');
    loginGate.id = 'login-gate';
    loginGate.innerHTML = `
      <div class="login-gate-content">
        <h1>
          <span class="gate-welcome">Welcome to</span><br>
          <span class="gate-title">Alex Guan's AI Knowledge Base</span>
        </h1>
        <p>Daily AI industry insights · Curated knowledge cards · Auto-collected and analyzed by AI</p>
        <button class="login-btn" onclick="auth.showLoginModal()">Sign In</button>
      </div>
    `;
    document.body.insertBefore(loginGate, document.body.firstChild);
  }
  loginGate.style.display = 'flex';
};

// 隐藏登录门控 - 显示内容
window.hideLoginGate = function() {
  const loginGate = document.getElementById('login-gate');
  if (loginGate) {
    loginGate.style.display = 'none';
  }
  
  // 添加 class 让 CSS 显示主内容
  document.body.classList.add('auth-ready');
};

// 立即尝试创建
if (!createAuthInstance()) {
  document.addEventListener('DOMContentLoaded', function() {
    if (!createAuthInstance()) {
      // 再等一下，等 supabaseClient 初始化
      setTimeout(createAuthInstance, 100);
    }
  });
}

// 点击外部关闭下拉菜单
document.addEventListener('click', (e) => {
  const dropdown = document.getElementById('user-dropdown');
  const btn = e.target.closest('.user-avatar-btn');
  if (dropdown && !btn && !e.target.closest('.user-dropdown')) {
    dropdown.style.display = 'none';
  }
});
