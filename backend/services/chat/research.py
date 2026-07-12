"""研究任务调度服务"""
import json

from sqlalchemy.orm import Session

from agents.graph import ResearchWorkflow
from config.database import SessionLocal
from models.chat import Message
from models.project import Report, Source
from websocket import manager

# 全局工作流实例
workflow = ResearchWorkflow()


class ResearchService:
    def __init__(self, db: Session):
        self.db = db
        from services.chat import ConversationService
        self.conv_service = ConversationService(db)

    async def start_research(self, conversation_id: int, user_id: int, topic: str) -> dict:
        """启动研究工作流"""
        # 1. 保存用户消息
        self.conv_service.add_message(
            conv_id=conversation_id,
            role="user",
            content=topic,
            msg_type="text",
        )

        # 2. 添加正在研究的状态消息
        status_msg = self.conv_service.add_message(
            conv_id=conversation_id,
            role="assistant",
            content="🔍 正在规划研究方案...",
            msg_type="agent_status",
        )

        # 3. 广播开始
        await manager.broadcast(conversation_id, {
            "type": "agent_status",
            "agent": "planner",
            "status": "running",
            "progress": 5,
            "message": "正在分析研究主题...",
        })

        # 4. 创建报告记录
        report = Report(
            conversation_id=conversation_id,
            title=topic,
            content="",
            status="generating",
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        # 5. 异步执行工作流（后台运行）
        import asyncio
        asyncio.create_task(self._run_workflow(conversation_id, user_id, topic, report.id))

        return {
            "success": True,
            "message": "研究已启动",
            "data": {
                "conversation_id": conversation_id,
                "report_id": report.id,
            },
        }

    async def _run_workflow(self, conversation_id: int, user_id: int, topic: str, report_id: int):
        """后台执行研究工作流并通过 WebSocket 推送进度"""
        # ⚠️ 重要：创建独立数据库会话
        # FastAPI 的 get_db() 在请求结束后会关闭 session
        # 后台任务必须使用自己的 session
        db = SessionLocal()
        from services.chat import ConversationService
        conv_service = ConversationService(db)

        try:
            # 注册进度回调
            async def progress_callback(status: str, progress: float, message: str):
                await manager.broadcast(conversation_id, {
                    "type": "agent_status",
                    "agent": status,
                    "status": "running",
                    "progress": progress,
                    "message": message,
                })

            # 推送各个阶段状态
            await progress_callback("planner", 10, "正在生成研究大纲...")
            result = await workflow.run(topic=topic, user_id=user_id, conversation_id=conversation_id)

            # 保存报告内容
            if result.get("final_report"):
                content = result["final_report"]
                # 添加参考资料附录
                if result.get("sources"):
                    content += "\n\n---\n## 参考资料\n"
                    for s in result["sources"]:
                        content += f"- [{s['index']}] {s['title']} — {s['url']}\n"

                report = db.query(Report).filter(Report.id == report_id).first()
                if report:
                    report.content = content
                    report.title = result.get("report_title", topic)
                    report.status = "completed"
                    db.commit()

                # 保存来源
                for s in result.get("sources", []):
                    source = Source(
                        report_id=report_id,
                        index=s["index"],
                        title=s["title"],
                        url=s["url"],
                        snippet=s.get("snippet", ""),
                    )
                    db.add(source)
                db.commit()

                # 添加助手最终消息
                conv_service.add_message(
                    conv_id=conversation_id,
                    role="assistant",
                    content=f"📄 研究报告已生成完成！\n\n{content[:500]}...\n\n[查看完整报告]",
                    msg_type="report",
                    metadata_json=json.dumps({"report_id": report_id}),
                )

                await manager.broadcast(conversation_id, {
                    "type": "report_completed",
                    "report_id": report_id,
                    "progress": 100,
                })

            else:
                # 报告生成失败
                error = result.get("error", "未知错误")
                conv_service.add_message(
                    conv_id=conversation_id,
                    role="assistant",
                    content=f"❌ 报告生成失败：{error}",
                    msg_type="error",
                )
                report = db.query(Report).filter(Report.id == report_id).first()
                if report:
                    report.status = "failed"
                    db.commit()

                await manager.broadcast(conversation_id, {
                    "type": "error",
                    "message": error,
                })

        except Exception as e:
            import traceback
            error_detail = f"{type(e).__name__}: {str(e)}"
            print(f"[ResearchWorker] ERROR: {error_detail}")
            traceback.print_exc()

            try:
                conv_service.add_message(
                    conv_id=conversation_id,
                    role="assistant",
                    content=f"❌ 系统错误：{error_detail}",
                    msg_type="error",
                )
                report = db.query(Report).filter(Report.id == report_id).first()
                if report:
                    report.status = "failed"
                    db.commit()
            except Exception:
                pass

            await manager.broadcast(conversation_id, {
                "type": "error",
                "message": error_detail,
            })

        finally:
            db.close()
