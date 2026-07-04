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

    const likeBtn = document.getElementById('like-btn');
    const likeCountEl = document.getElementById('like-count');
    if (!likeBtn) return;

    const isLiked = likeBtn.classList.contains('active');

    if (isLiked) {
      // 取消点赞
      const { error } = await supabaseClient
        .from('likes')
        .delete()
        .eq('user_id', auth.user.id)
        .eq('content_type', this.contentType)
        .eq('content_id', this.contentId);
      
      if (!error) {
        likeBtn.classList.remove('active');
        if (likeCountEl) {
          likeCountEl.textContent = Math.max(0, parseInt(likeCountEl.textContent) - 1);
        }
      }
    } else {
      // 点赞
      const { error } = await supabaseClient
        .from('likes')
        .insert({
          user_id: auth.user.id,
          content_type: this.contentType,
          content_id: this.contentId
        });
      
      if (!error) {
        likeBtn.classList.add('active');
        if (likeCountEl) {
          likeCountEl.textContent = parseInt(likeCountEl.textContent) + 1;
        }
      }
    }
  }

  // 切换收藏
  async toggleBookmark() {
    if (!auth.isLoggedIn()) {
      auth.showLoginModal();
      return;
    }

    const bookmarkBtn = document.getElementById('bookmark-btn');
    if (!bookmarkBtn) return;

    const isBookmarked = bookmarkBtn.classList.contains('active');

    if (isBookmarked) {
      const { error } = await supabaseClient
        .from('bookmarks')
        .delete()
        .eq('user_id', auth.user.id)
        .eq('content_type', this.contentType)
        .eq('content_id', this.contentId);
      
      if (!error) {
        bookmarkBtn.classList.remove('active');
      }
    } else {
      const { error } = await supabaseClient
        .from('bookmarks')
        .insert({
          user_id: auth.user.id,
          content_type: this.contentType,
          content_id: this.contentId
        });
      
      if (!error) {
        bookmarkBtn.classList.add('active');
      }
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
    const avatar = comment.profile?.avatar_url 
      ? `<img src="${comment.profile.avatar_url}" alt="" class="comment-avatar">`
      : `<span class="avatar-placeholder">${(comment.profile?.display_name || '?')[0].toUpperCase()}</span>`;
    
    return `
      <div class="comment" data-id="${comment.id}">
        <div class="comment-header">
          ${avatar}
          <span class="comment-author">${comment.profile?.display_name || 'Anonymous'}</span>
          <span class="comment-time">${timeAgo}</span>
          ${auth.isLoggedIn() && auth.user.id === comment.user_id ? `
            <button class="comment-delete" onclick="interactions.deleteComment('${comment.id}')">×</button>
          ` : ''}
        </div>
        <div class="comment-body">${this.escapeHtml(comment.body)}</div>
        <button class="comment-reply-btn" onclick="interactions.showReplyForm('${comment.id}')">回复</button>
        <div class="reply-form" id="reply-form-${comment.id}" style="display:none;">
          <textarea placeholder="回复..." maxlength="2000"></textarea>
          <button onclick="interactions.submitReply('${comment.id}')">发送</button>
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
      open: '🟡 待处理',
      in_progress: '🔵 处理中',
      replied: '🟢 已回复',
      closed: '⚫ 已关闭'
    };

    container.innerHTML = suggestions.map(s => `
      <div class="suggestion-item status-${s.status}">
        <div class="suggestion-header">
          <h3>${this.escapeHtml(s.title)}</h3>
          <span class="status-badge">${statusLabels[s.status] || s.status}</span>
        </div>
        <p>${this.escapeHtml(s.description)}</p>
        ${s.admin_reply ? `
          <div class="admin-reply">
            <strong>管理员回复：</strong>
            <p>${this.escapeHtml(s.admin_reply)}</p>
          </div>
        ` : ''}
        <time>${new Date(s.created_at).toLocaleDateString('zh-CN')}</time>
      </div>
    `).join('');
  }

  // 工具函数
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

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
