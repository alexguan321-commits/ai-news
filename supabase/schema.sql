-- AI News Website Supabase Schema
-- 用户认证、点赞、收藏、评论、工单系统

-- ============================================
-- 1. 用户表（扩展 Supabase Auth）
-- ============================================
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  username TEXT UNIQUE,
  display_name TEXT,
  avatar_url TEXT,
  role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 自动创建 profile
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, username, display_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'user_name',
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
    NEW.raw_user_meta_data->>'avatar_url'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- 2. 点赞表
-- ============================================
CREATE TABLE public.likes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  content_type TEXT NOT NULL CHECK (content_type IN ('report', 'card')),
  content_id TEXT NOT NULL,  -- e.g., "2026-07-04-morning"
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, content_type, content_id)
);

CREATE INDEX idx_likes_content ON public.likes(content_type, content_id);
CREATE INDEX idx_likes_user ON public.likes(user_id);

-- ============================================
-- 3. 收藏表
-- ============================================
CREATE TABLE public.bookmarks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  content_type TEXT NOT NULL CHECK (content_type IN ('report', 'card')),
  content_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, content_type, content_id)
);

CREATE INDEX idx_bookmarks_user ON public.bookmarks(user_id);

-- ============================================
-- 4. 评论表
-- ============================================
CREATE TABLE public.comments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  content_type TEXT NOT NULL CHECK (content_type IN ('report', 'card')),
  content_id TEXT NOT NULL,
  parent_id UUID REFERENCES public.comments(id) ON DELETE CASCADE,
  body TEXT NOT NULL CHECK (char_length(body) > 0 AND char_length(body) <= 2000),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comments_content ON public.comments(content_type, content_id);
CREATE INDEX idx_comments_user ON public.comments(user_id);
CREATE INDEX idx_comments_parent ON public.comments(parent_id);

-- ============================================
-- 5. 建议/工单表
-- ============================================
CREATE TABLE public.suggestions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL CHECK (char_length(title) > 0 AND char_length(title) <= 200),
  description TEXT NOT NULL CHECK (char_length(description) > 0 AND char_length(description) <= 5000),
  category TEXT DEFAULT 'feature' CHECK (category IN ('bug', 'feature', 'content', 'other')),
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'replied', 'closed')),
  admin_reply TEXT,
  replied_at TIMESTAMPTZ,
  replied_by UUID REFERENCES public.profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_suggestions_status ON public.suggestions(status);
CREATE INDEX idx_suggestions_user ON public.suggestions(user_id);

-- ============================================
-- 6. Row Level Security (RLS)
-- ============================================

-- 启用 RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suggestions ENABLE ROW LEVEL SECURITY;

-- Profiles: 所有人可读，本人可改
CREATE POLICY "Profiles are viewable by everyone" ON public.profiles
  FOR SELECT USING (true);

CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- Likes: 所有人可读，登录用户可增删自己的
CREATE POLICY "Likes are viewable by everyone" ON public.likes
  FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create likes" ON public.likes
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own likes" ON public.likes
  FOR DELETE USING (auth.uid() = user_id);

-- Bookmarks: 同上
CREATE POLICY "Bookmarks are viewable by everyone" ON public.bookmarks
  FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create bookmarks" ON public.bookmarks
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own bookmarks" ON public.bookmarks
  FOR DELETE USING (auth.uid() = user_id);

-- Comments: 所有人可读，登录用户可发，本人可删改
CREATE POLICY "Comments are viewable by everyone" ON public.comments
  FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create comments" ON public.comments
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own comments" ON public.comments
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own comments" ON public.comments
  FOR DELETE USING (auth.uid() = user_id);

-- Suggestions: 所有人可读自己的，admin 可读全部
CREATE POLICY "Users can view own suggestions" ON public.suggestions
  FOR SELECT USING (auth.uid() = user_id OR EXISTS (
    SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
  ));

CREATE POLICY "Authenticated users can create suggestions" ON public.suggestions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can update suggestions" ON public.suggestions
  FOR UPDATE USING (EXISTS (
    SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
  ));

-- ============================================
-- 7. 辅助函数
-- ============================================

-- 获取内容的点赞数
CREATE OR REPLACE FUNCTION public.get_like_count(p_content_type TEXT, p_content_id TEXT)
RETURNS INTEGER AS $$
  SELECT COUNT(*)::INTEGER FROM public.likes
  WHERE content_type = p_content_type AND content_id = p_content_id;
$$ LANGUAGE SQL STABLE;

-- 获取内容的评论数
CREATE OR REPLACE FUNCTION public.get_comment_count(p_content_type TEXT, p_content_id TEXT)
RETURNS INTEGER AS $$
  SELECT COUNT(*)::INTEGER FROM public.comments
  WHERE content_type = p_content_type AND content_id = p_content_id AND parent_id IS NULL;
$$ LANGUAGE SQL STABLE;

-- 检查用户是否已点赞
CREATE OR REPLACE FUNCTION public.has_liked(p_user_id UUID, p_content_type TEXT, p_content_id TEXT)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.likes
    WHERE user_id = p_user_id AND content_type = p_content_type AND content_id = p_content_id
  );
$$ LANGUAGE SQL STABLE;

-- 检查用户是否已收藏
CREATE OR REPLACE FUNCTION public.has_bookmarked(p_user_id UUID, p_content_type TEXT, p_content_id TEXT)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.bookmarks
    WHERE user_id = p_user_id AND content_type = p_content_type AND content_id = p_content_id
  );
$$ LANGUAGE SQL STABLE;
