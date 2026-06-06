# Giftee Wallet Tool

Tool desktop Windows để:

- Đăng nhập TL-APP bằng Chrome profile local.
- Scan link Giftee từ lịch sử `Rút nhanh`.
- Kiểm tra link nào đã nạp, link nào còn point.
- Nạp toàn bộ link còn sót vào Gift Wallet.

## Yêu cầu

- Windows.
- Google Chrome cài ở đường dẫn mặc định:
  `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Python 3.10+.
- Node.js 18+.

## Cài lần đầu

Mở terminal tại thư mục project rồi chạy:

```bat
install.bat
```

Hoặc chạy thủ công:

```bat
python -m pip install -r requirements.txt
npm install
```

## Chạy tool

```bat
run_giftee_desktop_tool_qt.bat
```

Lần đầu chạy, tool sẽ tạo thư mục Chrome profile local:

```text
giftee_chrome_profile
```

Bạn cần login Gift Wallet và TL-APP trong Chrome profile này. Những lần sau session sẽ được lưu local, không cần login lại nếu cookie chưa hết hạn.

## Flow sử dụng

1. Mở tool.
2. Tab `Lấy link TL-APP`:
   - Bấm `Chrome login TL-APP` nếu chưa login.
   - Bấm `Lấy link hôm nay` hoặc `Scan tất cả link`.
   - Tool sẽ tự lấy link và check trạng thái nạp.
3. Tab `Nạp vào ví`:
   - Tool mặc định dùng file `tl_app_links_chua_nap.txt`.
   - Bấm `Nạp toàn bộ link`.

## File tự sinh khi chạy

Các file này là dữ liệu local, không nên commit lên git:

- `giftee_chrome_profile/`
- `tl_app_links_today.txt`
- `tl_app_links_today.csv`
- `tl_app_giftee_check.csv`
- `tl_app_links_chua_nap.txt`
- `giftee_left_direct_results_gui.csv`

## File chính trong project

- `giftee_desktop_tool_qt.py`: giao diện desktop.
- `fetch_tl_app_links.js`: lấy link từ TL-APP.
- `check_tl_app_login.js`: kiểm tra login TL-APP.
- `check_wallet_login.js`: kiểm tra login Gift Wallet.
- `check_giftee_links_904.js`: kiểm tra link Giftee còn point hay đã nạp.
- `merge_giftee_left_direct.js`: nạp link còn sót vào Gift Wallet.

## Lưu ý bảo mật

Không commit thư mục `giftee_chrome_profile/` vì trong đó có cookie/session đăng nhập.
