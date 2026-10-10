# Security / 安全说明

## Intended deployment

pp Daily is an unauthenticated, single-user service for private Tailscale access. Run FastAPI on `127.0.0.1` behind Tailscale Serve HTTPS and restrict tailnet access to your own devices. Public source code does not mean the running service should be public. Do not enable Funnel, expose the port to the Internet, or use GitHub Pages as the backend.

本服务没有应用登录，只适合本人设备通过 Tailscale 私人 HTTPS 访问。后端监听本机，限制 tailnet 访问权限；公开的是源代码，不是个人打卡数据或服务入口。

## Data and trust boundaries

- SQLite and IndexedDB contain personal data; backups are not encrypted by the application.
- Keep a backup outside the Mac and protect it with your device/storage access controls.
- Offline timestamps come from the client. The server validates date consistency and project validity, but cannot prove that an unauthenticated offline client clock is honest.
- A restore replaces the dataset and changes its generation. Export unsynced data before reloading clients.
- The API is not designed for untrusted multi-user or public deployment.

## Reporting an issue

For non-sensitive issues, use GitHub Issues with synthetic data. For a security issue, use the repository's private vulnerability reporting feature if the owner has enabled it, or contact the owner privately through their GitHub profile. Do not put credentials, personal backups, private hostnames, or exploit details involving personal data in public issues.

安全问题请优先使用仓库已启用的私密漏洞报告入口，或通过维护者 GitHub 资料中提供的私人联系方式反馈。不要在公开 Issue 中上传凭据、个人数据库或备份。
