import { createClient } from '@supabase/supabase-js'
import { Suspense } from 'react'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// 不同行业的专属图标与色彩主题
const categoryStyles: Record<string, { bg: string; text: string; border: string; icon: string }> = {
  DeFi: { bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-800/50', icon: '🪙' },
  Layer2: { bg: 'bg-purple-950/60', text: 'text-purple-400', border: 'border-purple-800/50', icon: '⚡' },
  Regulation: { bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-800/50', icon: '⚖️' },
  Security: { bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-800/50', icon: '🛡️' },
  NFT: { bg: 'bg-pink-950/60', text: 'text-pink-400', border: 'border-pink-800/50', icon: '🎨' },
  Macro: { bg: 'bg-blue-950/60', text: 'text-blue-400', border: 'border-blue-800/50', icon: '🌐' },
  Other: { bg: 'bg-slate-800/60', text: 'text-slate-300', border: 'border-slate-700/50', icon: '📌' },
}

async function NewsList() {
  const { data: events, error } = await supabase
    .from('events')
    .select(`
      id,
      summary_title,
      summary_content,
      category,
      created_at,
      event_feed_mappings (
        raw_feeds (
          source_name,
          original_title,
          original_url,
          published_at
        )
      )
    `)
    .order('id', { ascending: false })

  if (error) {
    console.error('获取聚合数据失败:', error)
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 max-w-7xl mx-auto">
      {events?.map((event) => {
        const catStyle = categoryStyles[event.category] || categoryStyles['Other']
        
        return (
          <article 
            key={event.id}
            className="bg-slate-900 border border-slate-800 rounded-xl p-4 sm:p-5 flex flex-col justify-between shadow-lg"
          >
            <div>
              {/* 顶部标签（带行业图标）与日期 */}
              <div className="flex justify-between items-center mb-3 gap-2">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded border ${catStyle.bg} ${catStyle.text} ${catStyle.border}`}>
                  <span>{catStyle.icon}</span>
                  <span>{event.category}</span>
                </span>
                <span className="text-xs text-slate-500 whitespace-nowrap">
                  {new Date(event.created_at).toLocaleDateString()}
                </span>
              </div>

              {/* AI 精炼标题 */}
              <h2 className="text-base sm:text-lg font-semibold text-slate-100 mb-2 leading-snug">
                {event.summary_title}
              </h2>

              {/* AI 结构化摘要 */}
              <p className="text-sm text-slate-400 mb-4 leading-relaxed">
                {event.summary_content}
              </p>
            </div>

            {/* 底部：多源报道与历史追溯 */}
            <div className="border-t border-slate-800/80 pt-3 mt-2">
              <div className="text-xs text-slate-400 mb-2 font-medium">多源报道与历史追溯：</div>
              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {event.event_feed_mappings?.map((mapping: any, idx: number) => {
                  const feed = mapping.raw_feeds
                  if (!feed) return null
                  return (
                    <a
                      key={idx}
                      href={feed.original_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition border border-slate-700/50 max-w-full"
                    >
                      <span className="text-blue-400 font-medium shrink-0">[{feed.source_name}]</span>
                      <span className="truncate">{feed.original_title}</span>
                    </a>
                  )
                })}
              </div>
            </div>
          </article>
        )
      })}
    </div>
  )
}

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8">
      <header className="max-w-7xl mx-auto mb-8">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Web3 AI News Aggregator</h1>
        <p className="text-sm text-slate-400 mt-1">基于 Supabase 与 Gemini 自动聚合清洗的行业快讯流</p>
      </header>

      {/* 使用 Suspense 适配 cacheComponents 动态加载 */}
      <Suspense fallback={<div className="text-center text-slate-500 py-12">正在加载快讯数据...</div>}>
        <NewsList />
      </Suspense>
    </main>
  )
}