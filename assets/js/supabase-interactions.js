/**
 * Supabase 用户互动模块
 * 点赞、收藏、评论、建议
 */

class SupabaseInteractions {
  constructor() {
    this.contentType = null;
    this.contentId = null;
  }

  // 初始化当前页面内容
  init(contentType, contentId) {
    this.contentType = contentType;
    this.contentId = contentId;
    this.loadStats();
    this.loadUserState();
    this.initLockState();
    
    // 监听登录状态变化，登录后更新锁定状态
    if (typeof auth !== 'undefined' && auth.onChange) {
      auth.onChange((user) => {
        if (user) {
          // 用户登录了，移除锁定状态
          document.querySelectorAll('.interaction-btn.locked').forEach(btn => {
            btn.classList.remove('locked');
            btn.removeAttribute('data-tooltip');
          });
          // 重新加载用户状态（点赞/收藏状态）
          this.loadUserState();
        } else {
          // 用户登出了，重新添加锁定状态
          this.initLockState();
        }
      });
    }
  }

  // 初始化锁定状态（未登录用户）
  initLockState() {
    if (!auth.isLoggedIn()) {
      // 给点赞/收藏按钮添加锁定状态
      document.querySelectorAll('.interaction-btn').forEach(btn => {
        btn.classList.add('locked');
        btn.setAttribute('data-tooltip', '登录后即可使用');
      });
    }
  }

  // 加载统计数据（点赞数、评论数）
  async loadStats() {
    if (!this.contentType || !this.contentId) return;

    // 点赞数
    const { data: likes } = await supabaseClient
      .rpc('get_like_count', {
        p_content_type: this.contentType,
        p_content_id: this.contentId
      });
    
    const likeCountEl = document.getElementById('like-count');
    if (likeCountEl && likes !== null) {
      likeCountEl.textContent = likes;
    }

    // 评论数
    const { data: comments } = await supabaseClient
      .rpc('get_comment_count', {
        p_content_type: this.contentType,
        p_content_id: this.contentId
      });
    
    const commentCountEl = document.getElementById('comment-count');
    if (commentCountEl && comments !== null) {
      commentCountEl.textContent = comments;
    }
    
    // 同步更新 header 中的计数器
    const commentCountHeader = document.getElementById('comment-count-header');
    if (commentCountHeader && comments !== null) {
      commentCountHeader.textContent = comments;
    }
  }

  // 加载当前用户状态（是否已点赞/收藏）
  async loadUserState() {
    if (!auth.isLoggedIn() || !this.contentType || !this.contentId) return;

    // 是否已点赞
    const { data: liked } = await supabaseClient
      .rpc('has_liked', {
        p_user_id: auth.user.id,
        p_content_type: this.contentType,
        p_content_id: this.contentId
      });
    
    const likeBtn = document.getElementById('like-btn');
    if (likeBtn && liked) {
      likeBtn.classList.add('active');
    }

    // 是否已收藏
    const { data: bookmarked } = await supabaseClient
      .rpc('has_bookmarked', {
        p_user_id: auth.user.id,
        p_content_type: this.contentType,
        p_content_id: this.contentId
      });
    
    const bookmarkBtn = document.getElementById('bookmark-btn');
    if (bookmarkBtn && bookmarked) {
      bookmarkBtn.classList.add('active');
    }
  }

  // 切换点赞
  async toggleLike() {
    if (!auth.isLoggedIn()) {
      auth.showLoginModal();
      return;
    }
    if (this._togglingLike) return; // 防重复点击
    this._togglingLike = true;

    const likeBtn = document.getElementById('like-btn');
    const likeCountEl = document.getElementById('like-count');
    if (!likeBtn) { this._togglingLike = false; return; }

    const isLiked = likeBtn.classList.contains('active');
    const currentCount = parseInt(likeCountEl?.textContent || '0');

    // 乐观更新 + 禁用按钮
    likeBtn.classList.add('loading');
    if (isLiked) {
      likeBtn.classList.remove('active');
      if (likeCountEl) likeCountEl.textContent = Math.max(0, currentCount - 1);
    } else {
      likeBtn.classList.add('active');
      if (likeCountEl) likeCountEl.textContent = currentCount + 1;
    }

    try {
      if (isLiked) {
        const { error } = await supabaseClient
          .from('likes')
          .delete()
          .eq('user_id', auth.user.id)
          .eq('content_type', this.contentType)
          .eq('content_id', this.contentId);
        if (error) throw error;
      } else {
        const { error } = await supabaseClient
          .from('likes')
          .insert({
            user_id: auth.user.id,
            content_type: this.contentType,
            content_id: this.contentId
          });
        if (error) throw error;
      }
    } catch (e) {
      // 失败时回滚 UI
      console.error('Toggle like failed:', e);
      likeBtn.classList.toggle('active');
      if (likeCountEl) likeCountEl.textContent = currentCount;
    } finally {
      likeBtn.classList.remove('loading');
      this._togglingLike = false;
    }
  }

  // 切换收藏
  async toggleBookmark() {
    if (!auth.isLoggedIn()) {
      auth.showLoginModal();
      return;
    }
    if (this._togglingBookmark) return; // 防重复点击
    this._togglingBookmark = true;

    const bookmarkBtn = document.getElementById('bookmark-btn');
    if (!bookmarkBtn) { this._togglingBookmark = false; return; }

    const isBookmarked = bookmarkBtn.classList.contains('active');

    // 乐观更新 + 禁用按钮
    bookmarkBtn.classList.add('loading');
    if (isBookmarked) {
      bookmarkBtn.classList.remove('active');
    } else {
      bookmarkBtn.classList.add('active');
    }

    try {
      if (isBookmarked) {
        const { error } = await supabaseClient
          .from('bookmarks')
          .delete()
          .eq('user_id', auth.user.id)
          .eq('content_type', this.contentType)
          .eq('content_id', this.contentId);
        if (error) throw error;
      } else {
        const { error } = await supabaseClient
          .from('bookmarks')
          .insert({
            user_id: auth.user.id,
            content_type: this.contentType,
            content_id: this.contentId
          });
        if (error) throw error;
      }
    } catch (e) {
      // 失败时回滚 UI
      console.error('Toggle bookmark failed:', e);
      bookmarkBtn.classList.toggle('active');
    } finally {
      bookmarkBtn.classList.remove('loading');
      this._togglingBookmark = false;
    }
  }

  // 加载评论
  async loadComments() {
    if (!this.contentType || !this.contentId) return;

    const { data: comments, error } = await supabaseClient
      .from('comments')
      .select(`
        *,
        profile:profiles(display_name, avatar_url)
      `)
      .eq('content_type', this.contentType)
      .eq('content_id', this.contentId)
      .is('parent_id', null)
      .order('created_at', { ascending: false });

    const container = document.getElementById('comments-list');
    if (!container) return;

    if (error || !comments || comments.length === 0) {
      container.innerHTML = '<p class="no-comments">暂无评论，来说两句吧~</p>';
      return;
    }

    container.innerHTML = comments.map(c => this.renderComment(c)).join('');
  }

  renderComment(comment) {
    const timeAgo = this.getTimeAgo(new Date(comment.created_at));
    const safeAvatar = safeAvatarUrl(comment.profile?.avatar_url);
    const safeAuthor = escapeHtml(comment.profile?.display_name || 'Anonymous');
    const safeInitial = escapeHtml((comment.profile?.display_name || '?')[0].toUpperCase());
    const avatar = safeAvatar 
      ? `<img src="${safeAvatar}" alt="" class="comment-avatar">`
      : `<span class="avatar-placeholder">${safeInitial}</span>`;
    
    return `
      <div class="comment" data-id="${escapeHtml(comment.id)}">
        <div class="comment-header">
          ${avatar}
          <span class="comment-author">${safeAuthor}</span>
          <span class="comment-time">${escapeHtml(timeAgo)}</span>
          ${auth.isLoggedIn() && auth.user.id === comment.user_id ? `
            <button class="comment-delete" onclick="interactions.deleteComment('${escapeHtml(comment.id)}')">×</button>
          ` : ''}
        </div>
        <div class="comment-body">${escapeHtml(comment.body)}</div>
        <button class="comment-reply-btn" onclick="interactions.showReplyForm('${escapeHtml(comment.id)}')">回复</button>
        <div class="reply-form" id="reply-form-${escapeHtml(comment.id)}" style="display:none;">
          <textarea placeholder="回复..." maxlength="2000"></textarea>
          <button onclick="interactions.submitReply('${escapeHtml(comment.id)}')">发送</button>
        </div>
      </div>
    `;
  }

  // 提交评论
  async submitComment() {
    if (!auth.isLoggedIn()) {
      auth.showLoginModal();
      return;
    }

    const textarea = document.getElementById('comment-input');
    if (!textarea) return;

    const body = textarea.value.trim();
    if (!body) return;
    if (body.length > 2000) {
      alert('评论不能超过 2000 字');
      return;
    }

    const { error } = await supabaseClient
      .from('comments')
      .insert({
        user_id: auth.user.id,
        content_type: this.contentType,
        content_id: this.contentId,
        body: body
      });

    if (error) {
      alert('评论失败: ' + error.message);
      return;
    }

    textarea.value = '';
    this.loadComments();
    this.loadStats();
  }

  // 显示回复表单
  showReplyForm(commentId) {
    const form = document.getElementById(`reply-form-${commentId}`);
    if (form) {
      form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }
  }

  // 提交回复
  async submitReply(parentId) {
    if (!auth.isLoggedIn()) {
      auth.showLoginModal();
      return;
    }

    const form = document.getElementById(`reply-form-${parentId}`);
    const textarea = form?.querySelector('textarea');
    if (!textarea) return;

    const body = textarea.value.trim();
    if (!body) return;

    const { error } = await supabaseClient
      .from('comments')
      .insert({
        user_id: auth.user.id,
        content_type: this.contentType,
        content_id: this.contentId,
        parent_id: parentId,
        body: body
      });

    if (error) {
      alert('回复失败: ' + error.message);
      return;
    }

    textarea.value = '';
    form.style.display = 'none';
    this.loadComments();
  }

  // 删除评论
  async deleteComment(commentId) {
    if (!confirm('确定要删除这条评论吗？')) return;

    const { error } = await supabaseClient
      .from('comments')
      .delete()
      .eq('id', commentId)
      .eq('user_id', auth.user.id);

    if (error) {
      alert('删除失败: ' + error.message);
      return;
    }

    this.loadComments();
    this.loadStats();
  }

  // 提交建议
  async submitSuggestion() {
    if (!auth.isLoggedIn()) {
      auth.showLoginModal();
      return;
    }

    const title = document.getElementById('suggestion-title')?.value.trim();
    const description = document.getElementById('suggestion-desc')?.value.trim();
    const category = document.getElementById('suggestion-category')?.value || 'feature';

    if (!title || !description) {
      alert('请填写标题和描述');
      return;
    }

    const { error } = await supabaseClient
      .from('suggestions')
      .insert({
        user_id: auth.user.id,
        title,
        description,
        category
      });

    if (error) {
      alert('提交失败: ' + error.message);
      return;
    }

    alert('建议已提交，感谢反馈！');
    
    // 清空表单
    if (document.getElementById('suggestion-title')) {
      document.getElementById('suggestion-title').value = '';
    }
    if (document.getElementById('suggestion-desc')) {
      document.getElementById('suggestion-desc').value = '';
    }
  }

  // 加载我的建议
  async loadMySuggestions() {
    if (!auth.isLoggedIn()) return;

    const { data: suggestions, error } = await supabaseClient
      .from('suggestions')
      .select('*')
      .eq('user_id', auth.user.id)
      .order('created_at', { ascending: false });

    const container = document.getElementById('my-suggestions-list');
    if (!container) return;

    if (error || !suggestions || suggestions.length === 0) {
      container.innerHTML = '<p>暂无建议</p>';
      return;
    }

    const statusLabels = {
      submitted: '🟡 已提交',
      in_progress: '🔵 处理中',
      optimized: '🟢 已优化',
      closed: '⚫ 已关闭'
    };

    container.innerHTML = suggestions.map(s => {
      const submittedAt = new Date(s.created_at).toLocaleString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
      });
      const processedAt = s.processed_at 
        ? new Date(s.processed_at).toLocaleString('zh-CN', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
          })
        : '—';

      return `
      <div class="suggestion-item status-${s.status}">
        <div class="suggestion-header">
          <h3>${escapeHtml(s.title)}</h3>
          <span class="status-badge status-${s.status}">${statusLabels[s.status] || s.status}</span>
        </div>
        <p>${escapeHtml(s.description)}</p>
        ${s.admin_reply ? `
          <div class="admin-reply">
            <strong>管理员回复：</strong>
            <p>${escapeHtml(s.admin_reply)}</p>
          </div>
        ` : ''}
        <div class="suggestion-meta">
          <span>📤 提交：${submittedAt}</span>
          <span>✅ 完成：${processedAt}</span>
        </div>
      </div>
    `;
    }).join('');
  }

  // 工具函数 - 使用全局 escapeHtml (supabase-utils.js)
  // escapeHtml 已在 window.escapeHtml 中定义

  getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return '刚刚';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}天前`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months}个月前`;
    return `${Math.floor(months / 12)}年前`;
  }
}

// 全局实例
const interactions = new SupabaseInteractions();
