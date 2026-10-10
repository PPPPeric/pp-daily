# iPhone 15 acceptance / iPhone 15 验收

Primary target: iPhone 15, iOS 17+ Safari and Home Screen PWA. The app uses CSS viewport units, not physical display pixels. The desktop check uses 393 × 852 portrait and 852 × 393 landscape. Prefer portrait for everyday use. Other phone models remain outside the first-release acceptance scope.

第一版主目标是 iPhone 15，iOS 17+，Safari 和主屏幕 PWA。布局没有机型锁定；桌面仅作为开发预览，不承诺其他手机专项适配。

## Desktop layout checks / 桌面布局检查

- All four pages fit the portrait viewport without horizontal overflow.
- Long names wrap without covering completion or management buttons.
- Landscape preserves readable content, scrolling, and navigation.
- Forms use 16px text and controls have at least 44 CSS-pixel touch height.
- Safe-area CSS covers top, bottom, left, and right; dynamic height handles browser chrome.

四页无横向溢出；长名称不覆盖按钮；横屏保留滚动和导航；表单文字为 16px；触摸区域至少高 44 CSS 像素；安全区和动态视口均有处理。

## On-device checks / 真机检查

These must be completed on the actual iPhone and Mac; a desktop viewport cannot simulate Dynamic Island, Safari's keyboard behavior, storage eviction, or Home Screen installation faithfully.

1. Install from Safari via private HTTPS. Check the name and double-p icon.
2. Open in Safari and from the Home Screen. Check Dynamic Island, home indicator, browser bars, and rotation.
3. Add a long project name. Focus input, open the keyboard, save, and verify navigation is reachable.
4. Complete once; verify Today, Calendar, and Statistics agree. Repeated taps must not add records.
5. After the initial cache finishes, disconnect the network, complete another project, close and reopen the PWA, and confirm the record persists.
6. Reconnect Tailscale and return to the foreground. Confirm the queue clears and the server has one record for that project/date.
7. Cross Shanghai midnight. Confirm the day changes within the foreground retry interval, and the old queued record keeps its original date.
8. Export JSON to Files. Restore in a disposable test dataset, verify projects and records, and verify pre-restore server backup creation.
9. Restart and sign in to the Mac. Check the service, private HTTPS, and daily backup output.

依次验证主屏幕安装、灵动岛和底部安全区、键盘、旋转、每日一次、离线重开、恢复联网、上海零点、备份恢复及 Mac 登录后自动运行。测试恢复时使用测试数据；日常数据恢复前先备份。

Record the actual iOS version and results when performing these checks. Do not describe desktop checks as real-device compatibility certification.
