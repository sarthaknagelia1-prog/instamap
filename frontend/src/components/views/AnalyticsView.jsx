import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import {
  TrendingUp,
  Search,
  ChevronLeft,
  ChevronRight,
  Filter,
  Film,
  Layers,
  Image,
  ArrowUpDown
} from 'lucide-react';

export default function AnalyticsView({ creatorId }) {
  const [loading, setLoading] = useState(true);
  const [perfData, setPerfData] = useState(null);
  const [postsResponse, setPostsResponse] = useState({ posts: [], total_count: 0, page: 1, page_size: 20 });
  const [contentTypeFilter, setContentTypeFilter] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchPosts = (page = 1, type = contentTypeFilter, sort = sortBy, order = sortOrder) => {
    api.getCreatorPosts(creatorId, {
      content_type: type || undefined,
      sort_by: sort,
      order: order,
      page: page,
      page_size: 20,
    }).then((data) => {
      setPostsResponse(data);
      setCurrentPage(page);
    }).catch(() => {});
  };

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getAnalyticsPerformance(creatorId).catch(() => null),
      api.getCreatorPosts(creatorId, { page: 1, page_size: 20 }).catch(() => ({ posts: [], total_count: 0, page: 1, page_size: 20 })),
    ]).then(([perf, pRes]) => {
      if (!isMounted) return;
      setPerfData(perf);
      setPostsResponse(pRes);
      setLoading(false);
    });

    return () => { isMounted = false; };
  }, [creatorId]);

  const handleFilterChange = (type) => {
    setContentTypeFilter(type);
    fetchPosts(1, type, sortBy, sortOrder);
  };

  const handleSortChange = (col) => {
    const nextOrder = sortBy === col && sortOrder === 'desc' ? 'asc' : 'desc';
    setSortBy(col);
    setSortOrder(nextOrder);
    fetchPosts(1, contentTypeFilter, col, nextOrder);
  };

  if (loading) {
    return <LoadingSkeleton rows={6} height="h-16" />;
  }

  const breakdown = perfData?.metrics?.content_type_breakdown || {};

  // Filter posts client-side for search query
  const displayedPosts = (postsResponse.posts || []).filter(p => {
    if (!searchQuery) return true;
    const text = (p.caption_text || '') + (p.post_id || '');
    return text.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-black text-slate-900 tracking-tight">Performance Intelligence & Post Browser</h2>
        <p className="text-xs text-slate-500 mt-1">
          Quantitative engagement breakdowns across Reels, Carousels, and Images. Sortable post repository.
        </p>
      </div>

      {/* Format Comparison Breakdown Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {['reel', 'carousel', 'image'].map((fmt) => {
          const stats = breakdown[fmt] || {};
          const isTop = (perfData?.top_content_type || '').toLowerCase() === fmt;
          const Icon = fmt === 'reel' ? Film : fmt === 'carousel' ? Layers : Image;

          return (
            <div
              key={fmt}
              className={`bg-white rounded-xl border p-5 shadow-xs transition ${
                isTop ? 'border-indigo-500 ring-2 ring-indigo-500/10' : 'border-slate-200/90'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-indigo-600" />
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">{fmt}s</span>
                </div>
                {isTop && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                    Highest Distribution
                  </span>
                )}
              </div>

              <div className="text-2xl font-black text-slate-900 my-1">
                {stats.average_engagement_rate ? `${(stats.average_engagement_rate).toFixed(2)}%` : '--%'}
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-500 mt-3 pt-3 border-t border-slate-100">
                <div>
                  <span className="block text-[11px] text-slate-400">Avg Reach</span>
                  <span className="font-bold text-slate-700">{stats.average_reach?.toLocaleString() || '--'}</span>
                </div>
                <div>
                  <span className="block text-[11px] text-slate-400">Analyzed Posts</span>
                  <span className="font-bold text-slate-700">{stats.count || 0}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Filter and Post Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Format pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            {['', 'reel', 'carousel', 'image'].map((fmt) => (
              <button
                key={fmt}
                onClick={() => handleFilterChange(fmt)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition capitalize ${
                  contentTypeFilter === fmt ? 'bg-indigo-600 text-white shadow-xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {fmt || 'All Formats'}
              </button>
            ))}
          </div>

          {/* Search box */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search captions or ID..."
              className="pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 w-full sm:w-60"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto border border-slate-200 rounded-xl">
          <table className="w-full text-xs text-left border-collapse">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase text-[11px]">
              <tr>
                <th className="py-2.5 px-3">Post ID</th>
                <th className="py-2.5 px-3">Format</th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-slate-800" onClick={() => handleSortChange('timestamp')}>
                  <div className="flex items-center gap-1">
                    <span>Date</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-slate-800" onClick={() => handleSortChange('engagement_rate')}>
                  <div className="flex items-center gap-1">
                    <span>ER (%)</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-slate-800" onClick={() => handleSortChange('likes')}>
                  <div className="flex items-center gap-1">
                    <span>Likes</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-2.5 px-3">Comments</th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-slate-800" onClick={() => handleSortChange('reach')}>
                  <div className="flex items-center gap-1">
                    <span>Reach</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-2.5 px-3">Caption</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {displayedPosts.length > 0 ? (
                displayedPosts.map((p) => (
                  <tr key={p.id || p.post_id} className="hover:bg-slate-50/70 transition">
                    <td className="py-2.5 px-3 font-mono font-bold text-indigo-700">{p.post_id}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold capitalize bg-slate-100 text-slate-700">
                        {p.content_type || 'reel'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 font-mono">
                      {p.timestamp ? new Date(p.timestamp).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-900">
                      {(p.engagement_rate || 0).toFixed(2)}%
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-700">{p.likes_count?.toLocaleString() || 0}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-700">{p.comments_count?.toLocaleString() || 0}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-700">{p.reach?.toLocaleString() || 0}</td>
                    <td className="py-2.5 px-3 text-slate-500 max-w-xs truncate" title={p.caption_text}>
                      {p.caption_text || '—'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No posts matched the current filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-2">
          <span>Showing {displayedPosts.length} of {postsResponse.total_count || 0} posts</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchPosts(currentPage - 1)}
              disabled={currentPage <= 1}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono font-bold text-slate-700">Page {currentPage}</span>
            <button
              onClick={() => fetchPosts(currentPage + 1)}
              disabled={currentPage * 20 >= (postsResponse.total_count || 0)}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
