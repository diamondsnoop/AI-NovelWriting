from novelos.foundation.providers.base_provider import BaseProvider, ProviderRequest, ProviderResponse


class MockProvider(BaseProvider):
    provider_name = "mock"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        chapter = request.context.get("chapter_no", "unknown")
        title = request.context.get("project_title", "Untitled Project")
        if request.task_type == "plan_chapter":
            text = (
                f"# 第{chapter}章大纲\n\n"
                f"- 项目：{title}\n"
                f"- 本章目标：推进当前主线\n"
                f"- 本章事件：主角接收新任务，并遇到新的阻碍\n"
                f"- 本章结尾：留下下一章推进钩子\n"
            )
        else:
            outline = request.context.get("chapter_outline", "")
            text = (
                f"【{title}】第{chapter}章草稿\n\n"
                f"这是一个由 {self.provider_name}:{self.model_name} 生成的骨架草稿。\n"
                f"当前任务类型：{request.task_type}。\n\n"
                f"上下文摘要：{request.context.get('summary_hint', '暂无摘要。')}\n\n"
                f"章节大纲：\n{outline or '暂无大纲。'}\n"
            )
        return ProviderResponse(
            text=text,
            provider=self.provider_name,
            model=self.model_name,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            latency_ms=0,
        )
