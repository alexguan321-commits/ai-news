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
    // 获取当前 session
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (session) {
      this.user = session.user;
      await this.loadProfile();
    }

    // 监听 auth 变化
    supabaseClient.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session) {
        this.user = session.user;
        await this.loadProfile();
      } else if (event === 'SIGNED_OUT') {
        this.user = null;
        this.profile = null;
      }
      this.notifyListeners();
      this.updateUI();
    });

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

    if (this.isLoggedIn()) {
      authContainer.innerHTML = `
        <div class="user-menu">
          <button class="user-avatar-btn" onclick="auth.toggleUserDropdown()">
            ${this.profile?.avatar_url 
              ? `<img src="${this.profile.avatar_url}" alt="avatar">`
              : `<span class="avatar-placeholder">${(this.profile?.display_name || this.user.email || '?')[0].toUpperCase()}</span>`
            }
            <span class="user-name">${this.profile?.display_name || this.user.email?.split('@')[0] || 'User'}</span>
          </button>
          <div class="user-dropdown" id="user-dropdown" style="display:none;">
            <a href="/ai-news/bookmarks/" class="dropdown-item">⭐ 我的收藏</a>
            <a href="/ai-news/suggestions/" class="dropdown-item">💡 我的建议</a>
            ${this.isAdmin() ? '<a href="/ai-news/admin/" class="dropdown-item">🔧 管理后台</a>' : ''}
            <hr>
            <button class="dropdown-item" onclick="auth.signOut()">退出登录</button>
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
        <h2>登录 AI 资讯日报</h2>
        
        <div class="oauth-buttons">
          <button class="oauth-btn github" onclick="auth.signInWithOAuth('github')">
            <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
            使用 GitHub 登录
          </button>
          <button class="oauth-btn google" onclick="auth.signInWithOAuth('google')">
            <svg viewBox="0 0 24 24" width="20" height="20"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            使用 Google 登录
          </button>
        </div>

        <div class="divider">
          <span>或使用邮箱</span>
        </div>

        <form id="email-login-form" onsubmit="auth.handleEmailLogin(event)">
          <input type="email" id="login-email" placeholder="邮箱" required>
          <input type="password" id="login-password" placeholder="密码" required>
          <button type="submit" class="submit-btn">登录</button>
        </form>

        <p class="switch-form">
          没有账号？<a href="#" onclick="auth.showSignupForm(); return false;">注册</a>
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
      <h2>注册 AI 资讯日报</h2>
      
      <form id="signup-form" onsubmit="auth.handleSignup(event)">
        <input type="text" id="signup-name" placeholder="显示名称" required>
        <input type="email" id="signup-email" placeholder="邮箱" required>
        <input type="password" id="signup-password" placeholder="密码 (至少6位)" minlength="6" required>
        <button type="submit" class="submit-btn">注册</button>
      </form>

      <p class="switch-form">
        已有账号？<a href="#" onclick="auth.showLoginForm(); return false;">登录</a>
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

// 全局实例
const auth = new SupabaseAuth();

// 点击外部关闭下拉菜单
document.addEventListener('click', (e) => {
  const dropdown = document.getElementById('user-dropdown');
  const btn = e.target.closest('.user-avatar-btn');
  if (dropdown && !btn && !e.target.closest('.user-dropdown')) {
    dropdown.style.display = 'none';
  }
});
