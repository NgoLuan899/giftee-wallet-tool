# Giftee Wallet Tool

Tool desktop Windows để:

- Đăng nhập TL-APP bằng Chrome profile local.
- Scan link Giftee từ lịch sử `Rút nhanh`.
- Kiểm tra link nào đã nạp, link nào còn point.
- Nạp point còn sót vào Gift Wallet.

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
run_tool.bat
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
   - Sau khi scan xong, tool sẽ tự tạo file `pending_giftee_links.txt`.
   - Tab nạp sẽ dùng file còn sót này. Nếu file chưa có, hãy scan TL-APP trước.
   - Bấm `Nạp point vào ví`.

## File tự sinh khi chạy

Các file này được tạo sau khi chạy scan/nạp, không cần có sẵn khi clone code:

- `giftee_chrome_profile/`
- `tl_app_links_today.txt`
- `tl_app_links_today.csv`
- `giftee_scan_results.csv`
- `pending_giftee_links.txt`
- `wallet_merge_results.csv`

## File chính trong project

- `giftee_wallet_tool.py`: giao diện desktop.
- `scan_tl_app_history.js`: scan link từ lịch sử TL-APP.
- `verify_tl_app_session.js`: kiểm tra session TL-APP.
- `verify_wallet_session.js`: kiểm tra session Gift Wallet.
- `scan_giftee_links.js`: kiểm tra trạng thái link Giftee.
- `merge_giftee_points.js`: nạp point còn sót vào Gift Wallet.

## Lưu ý bảo mật

Không commit thư mục `giftee_chrome_profile/` vì trong đó có cookie/session đăng nhập.
