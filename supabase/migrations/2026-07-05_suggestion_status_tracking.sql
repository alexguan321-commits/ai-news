-- Migration: Suggestion status tracking overhaul
-- Date: 2026-07-05
-- Changes:
--   1. Rename status values: open → submitted, replied → optimized
--   2. Add processed_at column for tracking completion time
--   3. Update CHECK constraint for new status values

-- Step 1: Add processed_at column
ALTER TABLE public.suggestions ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

-- Step 2: Migrate existing status values
UPDATE public.suggestions SET status = 'submitted' WHERE status = 'open';
UPDATE public.suggestions SET status = 'optimized' WHERE status = 'replied';

-- Step 3: Drop old CHECK constraint and add new one
ALTER TABLE public.suggestions DROP CONSTRAINT IF EXISTS suggestions_status_check;
ALTER TABLE public.suggestions ADD CONSTRAINT suggestions_status_check 
  CHECK (status IN ('submitted', 'in_progress', 'optimized', 'closed'));

-- Step 4: Update default value
ALTER TABLE public.suggestions ALTER COLUMN status SET DEFAULT 'submitted';

-- Step 5: Set processed_at for already-completed suggestions
UPDATE public.suggestions 
SET processed_at = replied_at 
WHERE processed_at IS NULL AND replied_at IS NOT NULL;
