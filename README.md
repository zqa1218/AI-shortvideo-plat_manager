# 猫后台助手（桌面端）

基于 PySide6 的桌面应用，一站式管理 B站、小红书、抖音的内容发布与作品数据。图标：`assets/cat.png` / `assets/cat.ico`。

## 界面主题

侧边栏底部可切换四套主题，选择会保存到 `data/config.json`：

- 珊瑚云 · 浅色暖白（默认）：暖白纸面 + 图标珊瑚红主色。
- 霓虹夜航 · 深色科技：深炭底 + 霓虹珊瑚红 + 冰蓝点缀。
- 冰川数据 · 冷蓝浅色：图标天空蓝为主、珊瑚红作强调。
- 深海墨蓝 · 专业暗色：墨蓝底 + 珊瑚红主按钮 + 薄荷绿点缀。

主题预览图见 `docs/themes/`。

## 安装（发布包）

从 [Releases](https://github.com/zqa1218/AI-shortvideo-plat_manager/releases) 下载：

- `CatHelper-Setup-1.0.0.exe`：安装包，装到当前用户目录（`%LOCALAPPDATA%\Programs\猫后台助手`），创建开始菜单快捷方式、可选桌面图标、可在「应用和功能」卸载。
- `CatHelper-1.0.0-portable.zip`：免安装版，解压后直接运行 `猫后台助手.exe`。

两者都不需要管理员权限。安装包**不包含**第三方 `social-auto-upload`，因此首次使用只有「手动/半自动发布」可用；要启用自动发布与自动采集，见下一节。

## 自动发布依赖（可选）

自动发布与自动采集需要 [social-auto-upload](https://github.com/dreammis/social-auto-upload)：

```powershell
powershell -ExecutionPolicy Bypass -File tools\setup-vendor.ps1
```

脚本会把仓库克隆到 `vendor/social-auto-upload`、创建 `.venv`、安装依赖与 patchright 的 Chromium，并生成 `conf.py`。前置条件：Python 3.12、能访问 GitHub 与 PyPI。装完后回到「账号管理」扫码登录即可。

从源码运行时，若 `vendor/` 就在项目内，应用会自动找到它；安装版请在安装目录里执行上面的脚本（开始菜单里有「安装自动发布依赖」快捷方式）。

## 运行

```powershell
pip install -r requirements.txt
python -m app.main
```

或双击 `run.bat`。首次启动会在 `data/social.db` 创建本地 SQLite 数据库。

也可以直接运行已打包的 `dist/猫后台助手/猫后台助手.exe`。打包版的数据独立保存在该程序旁的 `data/` 目录；自动发布和采集仍依赖项目的 `vendor/social-auto-upload`，请不要只把 exe 单独移出项目。

## 一键构建发布包

```powershell
powershell -ExecutionPolicy Bypass -File build-release.ps1
```

会依次执行 PyInstaller 打包、生成安装载荷（剔除用户数据 `data/`）、压缩免安装包、用 Inno Setup 编译安装包，产物输出到 `release/`。

## 当前功能

- 发布中心：编辑标题/正文/标签/素材，勾选目标平台，保存草稿或发布；内容类型支持视频与图文笔记；素材可从本地或素材库选择。
- 发布预览：点击「预览效果」按目标平台检查标题、正文和标签；图文支持逐张翻图，视频支持播放、暂停与拖动进度，预览不会保存草稿或触发发布。
- 素材库：批量导入图片/视频，MD5 去重，缩略图网格（视频抽首帧），标签/类型/关键词筛选，「用于发布」一键回填发布中心。
- 素材表现回看：发布任务自动按文件路径关联素材，素材库点「发布与表现」可查看关联任务和按标题匹配的跨平台数据快照及汇总。
- 发布计划：勾选定时发布且时间在未来时保存为「已排期」，应用内调度器每分钟检查，到点自动调用 sau 发布；支持立即发布、取消排期，未来 3 天无计划时显示断更提醒。
- 图形化交互：发布中心用平台卡片选择目标，日期时间通过弹出的日历选择；发布计划用日历标记有排期的日期，点击日期即可筛选当天任务。
- 自动发布：已接入 social-auto-upload（`vendor/social-auto-upload`），视频走 `upload-video`，图文笔记走 `upload-note`（抖音/小红书，多图），支持定时与 B站分区；B站不支持图文会自动跳过。
- 半自动发布：自动打开各平台创作者后台（复用浏览器登录态），人工完成最终上传，任务状态跟踪为「待手动确认」。
- 发布任务：任务列表与每个平台的执行结果。
- 数据看板：任务统计卡片，手动录入各平台作品的播放/点赞/评论/收藏/分享数据。
- 账号管理：B站、小红书、抖音一键快速扫码，首次使用自动创建 default 账号；也支持多账号记录与登录态检查。

## 平台差异

三个平台不是"同一套流程换个网址"，支持的内容类型和各项上限都不同。规则集中声明在 `app/models.py` 的 `PLATFORMS` 里，发布前逐平台体检：

| 平台 | 支持类型 | 标题上限 | 图文图片 | 话题上限 | 专有参数 |
| --- | --- | --- | --- | --- | --- |
| B站 | 仅视频 | 80 字 | 不支持图文 | 12 个 | 分区 `tid` |
| 小红书 | 视频 / 图文 | 20 字 | 18 张 | 10 个 | — |
| 抖音 | 视频 / 图文 | 视频 30 字 / 图文 20 字 | 35 张 | 不限 | — |

- 发布前按目标平台逐个校验：勾了不支持的类型（例如 B站 + 图文）直接拦下；标题超长会提示并自动截断；话题超量自动丢弃。
- 每个平台单独执行、单独写结果，某个平台失败不会拖累其他平台，也不会再"等它超时才显示别人的成功"。
- 自动发布带超时保护：视频 15 分钟、图文 10 分钟，超时按失败记录，任务不会永远停在「发布中」。
- 失败原因会归类成中文：页面元素没出现（多为平台改版）、登录态失效、网络失败、超时。
- 抖音的视频页和图文页是两个不同页面，标题框选择器分别维护在 `vendor/social-auto-upload/uploader/douyin_uploader/main.py` 的 `DOUYIN_TITLE_SELECTORS` 中；平台改版时只改这里。

## 作品数据自动采集

在「数据看板」点击「自动采集作品数据」，会遍历账号管理中的全部账号，复用 social-auto-upload 的登录态（`vendor/social-auto-upload/cookies/`）抓取作品数据并写入看板：

- B站：走官方公开 API（`x/web-interface/nav` → `x/space/arc/search` → `archive/stat`），字段完整：播放/点赞/评论/收藏/分享/BV号/链接。
- 抖音 / 小红书：用 patchright 打开创作者后台内容管理页解析作品卡片；页面结构可能随平台改版变化，首次使用请核对首条数据。
- 每次采集生成一条新快照（`recorded_at`），可用于后续趋势分析。
- 每天定时采集：看板勾选「每天自动采集」并设置时间（默认 08:00），到点自动跑全部账号，当天不重复执行，自动采集不弹窗、只在看板显示上次结果；需保持应用打开。
- 采集失败时会保留调试文件到 `data/collector_debug/`（页面 HTML、卡片原文、截图），便于校准选择器。
- 采集脚本在 `collectors/`，由 vendor 虚拟环境独立执行，通过 JSON 与主程序通信。

## 自动发布使用步骤

1. 在「账号管理」顶部点击对应平台的「扫码」按钮，在弹出的窗口中完成扫码；首次使用会自动创建 default 账号。
   抖音和小红书会强制显示浏览器窗口，B站在终端显示二维码。
2. 需要区分多个账号时，可在下方手动添加昵称，再选中账号扫码登录。
3. 回到「发布中心」，发布方式选择「自动发布」，选择视频文件并勾选平台，点击发布。
4. 在「发布任务」查看每个平台的成功/失败与日志尾部。

注意：B站发布默认分区 `tid=249`，可在发布中心修改；定时发布填写 `yyyy-MM-dd HH:mm`。

## social-auto-upload 环境（已装好，无需重复执行）

```powershell
python -m venv vendor/social-auto-upload/.venv
vendor/social-auto-upload/.venv/Scripts/python -m pip install -e vendor/social-auto-upload
vendor/social-auto-upload/.venv/Scripts/patchright install chromium
Copy-Item vendor/social-auto-upload/conf.example.py vendor/social-auto-upload/conf.py
```

## 目录结构

```
app/
  main.py            入口
  models.py          平台能力表、任务与状态定义
  database.py        SQLite 存取
  collectors.py      采集调度（调用 collectors/）
  publishers/        发布适配器（manual 半自动 / sau 自动）
  ui/                各页面、发布线程与主题
collectors/          B站 / 浏览器采集脚本（在 vendor 虚拟环境里执行）
tools/               setup-vendor.ps1：安装自动发布依赖
packaging/           installer.iss：Inno Setup 安装包脚本
assets/              图标
docs/                主题预览图
```

## 重新打包

```powershell
powershell -ExecutionPolicy Bypass -File build-release.ps1
```

只打 exe（不生成安装包）时：

```powershell
pyinstaller --noconfirm "猫后台助手.spec"
```

项目固定使用 PySide6 6.8.3，避免新版 Qt 与当前 PyInstaller 组合出现 DLL 加载问题。exe 的版本信息来自 `version_info.txt`。开机自启可在侧边栏直接勾选。

## 注意

自动发布与数据采集涉及各平台使用条款，请控制频率并先在测试账号验证。
