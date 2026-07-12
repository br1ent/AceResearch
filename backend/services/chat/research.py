"""研究任务调度服务（两阶段：规划 → 用户确认 → 执行）"""
import json

from sqlalchemy.orm import Session

from agents.graph import PlanningWorkflow, ExecutionWorkflow
from config.database import SessionLocal
from models.chat import Message
from models.project import Report, Source
from websocket import manager

planning_workflow = PlanningWorkflow()
execution_workflow = ExecutionWorkflow()


class ResearchService:
    def __init__(self, db: Session):
        self.db = db
        from services.chat import ConversationService
        self.conv_service = ConversationService(db)

    async def start_research(self, conversation_id: int, user_id: int, topic: str) -> dict:
        """阶段1：启动研究 → 仅运行 Planner，生成大纲后等待用户确认"""
        self.conv_service.add_message(conv_id=conversation_id, role="user", content=topic, msg_type="text")
        self.conv_service.add_message(conv_id=conversation_id, role="assistant", content="🔍 正在分析研究主题，生成研究方案...", msg_type="agent_status")

        # 创建报告记录
        report = Report(conversation_id=conversation_id, title=topic, content="", status="planning")
        self.db.add(report); self.db.commit(); self.db.refresh(report)

        # 广播开始
        await manager.broadcast(conversation_id, {"type": "agent_status", "agent": "planner", "status": "running", "progress": 5, "message": "正在生成研究大纲..."})

        # 后台运行 Planner
        import asyncio
        asyncio.create_task(self._run_planning(conversation_id, user_id, topic, report.id))

        return {"success": True, "message": "研究已启动", "data": {"conversation_id": conversation_id, "report_id": report.id}}

    async def _run_planning(self, conversation_id: int, user_id: int, topic: str, report_id: int):
        """后台运行 Planner 并推送方案给用户确认"""
        db = SessionLocal()
        try:
            result = await planning_workflow.run(topic=topic, user_id=user_id, conversation_id=conversation_id)

            outline = result.get("outline", [])
            subtasks = result.get("subtasks", [])
            report_title = result.get("report_title", topic)

            # 更新报告标题
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.title = report_title
                report.content = json.dumps({"outline": outline, "subtasks": [dict(s) for s in subtasks]}, ensure_ascii=False)
                report.status = "awaiting_confirm"
                db.commit()

            # 保存 Planner 结果作为消息
            plan_text = f"## 📋 研究方案\n\n**报告标题**：{report_title}\n\n**大纲**：\n"
            for o in outline:
                plan_text += f"- {o}\n"
            plan_text += "\n**研究子任务**：\n"
            for i, s in enumerate(subtasks, 1):
                plan_text += f"{i}. **{s['title']}** — {s['description']}\n"

            from services.chat import ConversationService
            conv_service = ConversationService(db)
            conv_service.add_message(conv_id=conversation_id, role="assistant", content=plan_text, msg_type="plan_ready",
                                     metadata_json=json.dumps({"report_id": report_id, "outline": outline, "subtasks": [dict(s) for s in subtasks]}, ensure_ascii=False))

            await manager.broadcast(conversation_id, {
                "type": "plan_ready",
                "report_id": report_id,
                "outline": outline,
                "subtasks": [dict(s) for s in subtasks],
                "progress": 20,
            })
        except Exception as e:
            import traceback
            print(f"[Planning] ERROR: {e}"); traceback.print_exc()
            await manager.broadcast(conversation_id, {"type": "error", "message": str(e)})
        finally:
            db.close()

    async def confirm_and_execute(self, conversation_id: int, user_id: int, report_id: int) -> dict:
        """阶段2：用户确认方案后 → 执行 Researcher→Analyst→Writer→Reviewer"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report or report.status != "awaiting_confirm":
            return {"success": False, "message": "报告状态异常，无法继续"}

        # 从 report.content 恢复规划结果
        plan_data = json.loads(report.content) if report.content else {}
        outline = plan_data.get("outline", [])
        subtasks = plan_data.get("subtasks", [])

        report.status = "generating"
        self.db.commit()

        # 添加确认消息
        self.conv_service.add_message(conv_id=conversation_id, role="user", content="✅ 确认方案，开始研究", msg_type="text")
        self.conv_service.add_message(conv_id=conversation_id, role="assistant", content="🔍 正在搜索资料...", msg_type="agent_status")

        await manager.broadcast(conversation_id, {"type": "agent_status", "agent": "researcher", "status": "running", "progress": 25, "message": "正在搜索资料..."})

        import asyncio
        asyncio.create_task(self._run_execution(conversation_id, user_id, outline, subtasks, report_id))

        return {"success": True, "message": "研究执行已启动"}

    async def _run_execution(self, conversation_id: int, user_id: int, outline, subtasks, report_id: int):
        """后台执行完整研究流程"""
        db = SessionLocal()
        try:
            from services.chat import ConversationService
            conv_service = ConversationService(db)

            state = {
                "topic": "", "user_id": user_id, "conversation_id": conversation_id,
                "outline": outline, "subtasks": subtasks,
                "search_results": [], "analysis": "",
                "report_title": "", "report_draft": "", "final_report": "", "sources": [],
                "status": "running", "progress": 25.0, "error": None, "reviewer_retries": 0,
            }

            result = await execution_workflow.run(state)

            if result.get("final_report"):
                content = result["final_report"]
                if result.get("sources"):
                    content += "\n\n---\n## 参考资料\n"
                    for s in result["sources"]:
                        content += f"- [{s['index']}] {s['title']} — {s['url']}\n"

                report = db.query(Report).filter(Report.id == report_id).first()
                if report:
                    report.content = content
                    report.status = "completed"
                    db.commit()

                for s in result.get("sources", []):
                    db.add(Source(report_id=report_id, index=s["index"], title=s["title"], url=s["url"], snippet=s.get("snippet", "")))
                db.commit()

                conv_service.add_message(conv_id=conversation_id, role="assistant",
                    content=f"📄 研究报告已生成！\n\n{content[:500]}...", msg_type="report",
                    metadata_json=json.dumps({"report_id": report_id}))

                await manager.broadcast(conversation_id, {"type": "report_completed", "report_id": report_id, "progress": 100})
            else:
                error = result.get("error", "未知错误")
                conv_service.add_message(conv_id=conversation_id, role="assistant", content=f"❌ 报告生成失败：{error}", msg_type="error")
                report = db.query(Report).filter(Report.id == report_id).first()
                if report: report.status = "failed"; db.commit()
                await manager.broadcast(conversation_id, {"type": "error", "message": error})
        except Exception as e:
            import traceback
            error_detail = f"{type(e).__name__}: {str(e)}"
            print(f"[Execution] ERROR: {error_detail}"); traceback.print_exc()
            await manager.broadcast(conversation_id, {"type": "error", "message": error_detail})
        finally:
            db.close()
