/**
 * 浏览统计模块
 * 记录页面访问次数，防刷机制（每人每天每内容只计一次）
 * 登录用户会记录 user_id，匿名用户用 visitor_id
 */

class PageViewTracker {
  constructor() {
    this.visitorId = this.getOrCreateVisitorId();
  }

  // 获取或创建匿名访客 ID
  getOrCreateVisitorId() {
    let visitorId = localStorage.getItem('visitor_id');
    if (!visitorId) {
      visitorId = 'v_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
      localStorage.setItem('visitor_id', visitorId);
    }
    return visitorId;
  }

  // 记录页面浏览
  async trackView(contentType, contentId) {
    if (!contentType || !contentId) return;

    // 检查是否今天已经记录过（防刷）
    const today = new Date().toISOString().split('T')[0];
    const viewKey = `viewed_${contentType}_${contentId}_${today}`;
    if (localStorage.getItem(viewKey)) {
      return; // 今天已记录，跳过
    }

    // 准备记录数据
    const viewData = {
      content_type: contentType,
      content_id: contentId,
      visitor_id: this.visitorId
    };

    // 如果用户已登录，记录 user_id
    if (typeof auth !== 'undefined' && auth.isLoggedIn()) {
      viewData.user_id = auth.user.id;
    }

    try {
      const { error } = await supabaseClient
        .from('page_views')
        .insert(viewData);

      if (!error) {
        // 标记今天已记录
        localStorage.setItem(viewKey, '1');
      }
    } catch (e) {
      console.error('Failed to track page view:', e);
    }
  }

  // 获取浏览次数
  async getViewCount(contentType, contentId) {
    if (!contentType || !contentId) return 0;

    try {
      const { data, error } = await supabaseClient
        .rpc('get_view_count', {
          p_content_type: contentType,
          p_content_id: contentId
        });

      if (error) {
        console.error('Failed to get view count:', error);
        return 0;
      }

      return data || 0;
    } catch (e) {
      console.error('Failed to get view count:', e);
      return 0;
    }
  }

  // 显示浏览次数
  async displayViewCount(elementId, contentType, contentId) {
    const count = await this.getViewCount(contentType, contentId);
    const element = document.getElementById(elementId);
    if (element) {
      element.textContent = count;
      element.closest('.view-count-wrapper')?.classList.remove('loading');
    }
  }

  // 获取热门内容
  async getPopularContent(contentType, limit = 10) {
    try {
      const { data, error } = await supabaseClient
        .rpc('get_popular_content', {
          p_content_type: contentType,
          p_limit: limit
        });

      if (error) {
        console.error('Failed to get popular content:', error);
        return [];
      }

      return data || [];
    } catch (e) {
      console.error('Failed to get popular content:', e);
      return [];
    }
  }
}

// 全局实例
const pageViews = new PageViewTracker();
