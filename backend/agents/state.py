from typing import TypedDict, Optional, List


class ResearchSubtask(TypedDict):
    """研究子任务"""
    id: str
    title: str
    description: str
    status: str  # pending / searching / completed / failed


class SearchResultItem(TypedDict):
    """单条搜索结果"""
    title: str
    url: str
    content: str
    score: float


class SourceItem(TypedDict):
    """引用来源（带编号，用于报告中标注）"""
    index: int
    title: str
    url: str
    snippet: str


class ResearchState(TypedDict):
    """LangGraph 研究状态"""

    # 输入
    topic: str
    user_id: int
    conversation_id: int

    # 规划阶段
    outline: List[str]                  # 报告大纲（章节列表）
    subtasks: List[ResearchSubtask]     # 研究子任务

    # 搜索阶段
    search_results: List[SearchResultItem]  # 所有搜索结果汇总

    # 分析阶段
    analysis: str                       # 综合分析文本

    # 写作阶段
    report_title: str                   # 报告标题
    report_draft: str                   # 报告草稿
    final_report: str                   # 最终报告
    sources: List[SourceItem]           # 引用来源列表（带编号）

    # 控制
    status: str                         # running / planning / searching / analyzing / writing / reviewing / completed / failed
    progress: float                     # 总体进度 0~100
    error: Optional[str]                # 错误信息
    reviewer_retries: int               # 审查重试次数
    reviewer_feedback: Optional[str]    # 审查不通过时的反馈意见（传给 Writer 修改用）
