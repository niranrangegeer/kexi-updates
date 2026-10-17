# 课习 · 课程与软件更新

此仓库用于发布课习 App 安装包、离线课程包和在线更新目录。

## 安装与使用

到 [Releases](https://github.com/niranrangegeer/kexi-updates/releases) 下载 kexi-0.3.0.apk，覆盖安装旧版本，不先卸载。
打开 App → 我的 → 云课程与软件更新 → 检查更新。下载课程后在课程管理中切换。
课程更新保留仍存在 ID 对应的掌握度、错题和复习记录，删除的内容对应记录不保留。
软件更新下载完成后点击安装，允许安装来源后返回再点一次；系统仍要求确认安装。

## 以后直接在 GitHub 页面更新课程

1. 准备课程 ZIP，根目录为 course.json 和对应 JSON，字段保持原课程 Schema。
2. 命名为 courseId-v版本号.zip，例如 engineering_fatigue_fracture-v2.zip。版本号必须递增且 courseId 与包内一致。
3. Releases → Draft a new release → 填写新标签，上传 ZIP，点击 Publish release。不要选 Pre-release。
4. Actions → “更新云课程与软件目录”运行成功后，catalog.json 会自动生成，App 检查更新即可看到。
5. 如自动任务失败，请打开该任务日志。修正附件后在 Actions 中 Run workflow 重试。已发布的旧课程无需每次重复上传。

## 软件升级

上传新 APK，并在同一 Release 上传 app-release.json，例如：

    {"versionCode":4,"versionName":"0.4.0","file":"kexi-0.4.0.apk","notes":"版本说明"}

APK 必须使用原签名与 com.kexi.app 包名，versionCode 持续递增；仅改上述 JSON 不能改变 APK 内部版本。
自动任务会计算附件大小与 SHA-256。签名私钥不存放在本仓库，也不放入 App。

## 发布机制

- catalog.json：App 固定读取的版本目录。只维护外部版本信息，不改变课程包字段。
- .github/workflows/update-catalog.yml：发布后更新目录，也可手动触发。
- scripts/publish_catalog.py：从非草稿、非预发布 Releases 选择每门课程最高版本与最高 APK 版本。
- App 首次接入联网更新需要安装 0.3.0；0.1/0.2 没有联网模块。
- GitHub 网络不可达时，已下载课程仍可离线使用。联网下载与安装尚需在实际手机和网络下验收。
