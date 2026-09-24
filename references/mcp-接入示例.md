# 达芬奇 MCP 接入示例

> 配套：本 skill 的 `references/官方开发文档蒸馏.md`（Scripting API 对象模型与签名索引）。
> 版本基准：**21.1**。

## 1. 现状与定位

- DaVinci Resolve **没有官方 MCP（Model Context Protocol）server**。
- 但它提供**完整的 Scripting API**（Python / Lua，见蒸馏稿 §2），可在外部进程里直接控制 Resolve 的全部功能——建项目、导媒体、剪时间线、调色、渲染。
- 因此「达芬奇 MCP」= 把 Scripting API **包装一层 MCP 传输 + tool 暴露**，让任意支持 MCP 的 Agent（Claude、WorkBuddy、Cursor 等）能像调工具一样驱动 Resolve。
- 本文件给两种落地路线；**具体社区 server 包名请以实测 / 插件市场为准，本文不绑定任何未经验证的第三方包**。

## 2. 路线 A：直接用 Scripting API 控制（最简，不需 MCP）

适合「本机脚本自动化」或「自己写一个小服务」。最小流程（来自蒸馏稿 §2.5）：

```python
import DaVinciResolveScript as dvr
resolve = dvr.scriptapp("Resolve")

pm = resolve.GetProjectManager()
proj = pm.LoadProject("MyProject") or pm.CreateProject("MyProject")
mp = proj.GetMediaPool()
folder = mp.GetRootFolder()
clips = mp.ImportMedia([{"FilePath": r"D:\footage\clip.mov"}])
mp.AppendToTimeline([{"mediaPoolItem": clips[0]}])

tl = proj.GetCurrentTimeline()
print("当前时间线:", tl.GetName(), "片段数:", len(tl.GetItemListInTrack("video", 1)))
```

**运行前提**（详见蒸馏稿 §2.1）：

- Resolve 已启动（外部脚本需 Resolve 在运行）；无界面可用 `-nogui` 启动。
- 外部 Python 需设环境变量：`RESOLVE_SCRIPT_API`、`RESOLVE_SCRIPT_LIB`，并把 `fusionscript.dll` / `DaVinciResolveScript.py` 所在目录加入 `PYTHONPATH`（Windows 下 `fusionscript.dll` 在 Resolve 程序目录）。
- 局域网远程控制需开启 **External scripting = Local/Network**（Studio 专属，端口 1144）。

## 3. 路线 B：把 Scripting API 包装成 MCP server（让 Agent 能直接调）

**通用架构**（不依赖特定 SDK，示意）：

```
Agent (Claude / WorkBuddy / Cursor)
        │  MCP (stdio / http)
        ▼
resolve-mcp server  ── 进程内 import DaVinciResolveScript ──► Resolve
   ├─ tool: resolve_load_project(name)
   ├─ tool: resolve_import_and_append(file_path)
   ├─ tool: resolve_set_clip_speed(timeline, clip, speed)
   ├─ tool: resolve_start_render(preset)
   └─ ... 每个 tool 内部调用蒸馏稿里的对应 API
```

### 3.1 客户端配置骨架（mcp.json / claude_desktop_config.json 风格）

```json
{
  "mcpServers": {
    "resolve": {
      "command": "python",
      "args": ["/abs/path/to/resolve_mcp_server.py"],
      "env": {
        "RESOLVE_SCRIPT_API": "http://127.0.0.1:1144",
        "RESOLVE_SCRIPT_LIB": "C:/Program Files/Blackmagic Design/DaVinci Resolve/fusionscript.dll",
        "PYTHONPATH": "C:/Program Files/Blackmagic Design/DaVinci Resolve"
      }
    }
  }
}
```

> 上面 `env` 路径为 Windows 示例；macOS 下在 `Resolve.app/Contents/MacOS` 内找 `fusionscript` / `DaVinciResolveScript.py`。**具体字段名以你选用的 MCP server 实现为准。**
> 社区已有把 Scripting API 暴露为 MCP tool 的第三方实现，可用关键词「DaVinci Resolve MCP server」「resolve-mcp」检索；选用前请核对它基于的 Scripting API 版本与你的 Resolve 版本是否匹配。

### 3.2 一个 tool 的 Python 骨架（示意，按所用 MCP SDK 调整）

```python
# 以「把媒体导入并追加到时间线」为例，内部就是蒸馏稿对象树的一串调用
def resolve_import_and_append(file_path: str) -> dict:
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() or pm.CreateProject("MCP_Project")
    mp = proj.GetMediaPool()
    clips = mp.ImportMedia([{"FilePath": file_path}])
    if not clips:
        return {"ok": False, "error": "导入失败，检查路径/格式"}
    mp.AppendToTimeline([{"mediaPoolItem": clips[0]}])
    return {"ok": True, "timeline": proj.GetCurrentTimeline().GetName()}
```

把函数签名与返回，按你用的 MCP SDK（如 FastMCP / 官方 `mcp` Python SDK）注册成 tool 即可。

## 4. 与蒸馏稿对象树对照（写 tool 时照此调用）

```
Resolve.GetProjectManager() → ProjectManager
  └─ LoadProject / CreateProject
Project.GetMediaPool()      → MediaPool
  └─ ImportMedia / AppendToTimeline / CreateTimelineFromClips
Project.GetCurrentTimeline()→ Timeline
  └─ GetItemListInTrack / SetSpeed(clip) / Export / GetNodeGraph
TimelineItem.SetSpeed(...)  → 变速（对应「曲线变速」问题）
Graph.ApplyGradeFromDRX / SetLUT → 调色
Project.StartRendering(jobIds) → 渲染
```

## 5. 注意事项（来自蒸馏稿 §2.4，写 tool 必看）

- **Studio / AI 专有**：Free 版调 Studio 函数返回 `False`（如 `GenerateSpeech`、多机位 AI 切换）。写 tool 时做好分支。
- **弃用 API**：`GetSetting(name)` → `GetSettings()` 取 dict；`AppendToTimeline(clips)` → `AppendToTimeline([AppendClipInfo])`；渲染用 `jobId` 字符串而非索引。
- **设置是 key-value 字典**：`Project.GetSettings()/SetSettings(dict)`、媒体池条目 `GetClipProperty()/SetClipProperty(name,value)` 与 UI 参数名一一对应；改前在 UI 设一次、对照快照即知 key。
- **错误处理**：每个 API 都可能返回 `None`/`False`，tool 里务必判空，把错误信息回传给 Agent。
- **版本**：API 随版本演进，以用户本机实时 `Support/Developer/Scripting/DaVinciResolveScript.pyi` 为准（见 SKILL.md「官方文档」一节）。
