"""
Issue analyzer module for analyzing GitLab issues using AI.

This module integrates with AI providers (OpenRouter, OpenAI) via OpenAI-compatible APIs
to analyze issues using the WWWH-TR framework.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from src.exceptions import AnalysisError
from src.image_url_converter import convert_relative_image_urls
from src.reporter import get_fixed_html_template

logger = logging.getLogger(__name__)

# Vietnamese prompt template for AI analysis
SYSTEM_PROMPT = """Bạn là một chuyên gia phân tích dự án phần mềm. Nhiệm vụ của bạn là phân tích ticket dự án phần mềm theo khung tư duy WWWH-TR và đưa ra các insight có thể hành động được. Hãy xem xét tất cả thông tin có sẵn bao gồm comments, related issues, và attachments.

QUAN TRỌNG: TẤT CẢ nội dung phân tích (TL;DR, Action Items, Open Questions, W1-W3, H, T, R) PHẢI được viết bằng TIẾNG VIỆT. Không được sử dụng tiếng Anh hoặc ngôn ngữ khác cho các phần phân tích."""

USER_PROMPT_TEMPLATE = """Phân tích ticket dự án phần mềm sau đây theo khung tư duy WWWH-TR.



────────────────────────────────

0. GIỚI THIỆU VỀ HỆ THỐNG (SYSTEM CONTEXT)

────────────────────────────────

UNIOSS3 là nền tảng thương mại điện tử toàn diện được thiết kế đặc biệt để quản lý hệ thống Furusato Nozei (quyên góp thuế quê hương) tại Nhật Bản. Hệ thống cho phép các đô thị nhận quyên góp từ công dân và cung cấp sản phẩm địa phương hoặc dịch vụ làm quà cảm ơn.

Mục đích kinh doanh chính:
1. Nhận quyên góp: Công dân thực hiện quyên góp được khấu trừ thuế cho các đô thị
2. Quản lý sản phẩm: Đô thị cung cấp sản phẩm địa phương làm "quà cảm ơn" cho quyên góp
3. Xử lý đơn hàng: Xử lý đơn quyên góp từ cả cửa hàng trực tuyến và máy bán hàng vật lý
4. Theo dõi tài chính: Quản lý deals, invoices và thanh toán giữa các bên (đô thị, nhà sản xuất, đại lý, v.v.)
5. Thưởng người dùng: Vận hành hệ thống điểm thưởng dựa trên xu (coins) nơi người dùng kiếm và tiêu xu

────────────────────────────────

CÁC THỰC THỂ CHÍNH VÀ VAI TRÒ

────────────────────────────────

1. Stores (Cửa hàng / Đô thị)
- Mỗi đô thị vận hành một "cửa hàng" trên nền tảng
- Loại: Trang quyên góp thuế (納税サイト) hoặc cửa hàng thương mại thông thường (一般ストア)
- Mục đích: Nhận quyên góp, hiển thị sản phẩm, quản lý đơn hàng
- Ví dụ: "Kyoto City Store" nhận quyên góp và cung cấp rượu sake địa phương làm quà cảm ơn

2. Orders (Đơn hàng)
- Đơn quyên góp hoặc mua hàng do người dùng thực hiện
- Loại: Đơn quyên góp thuế (納税注文) - quyên góp được khấu trừ thuế, hoặc đơn mua hàng (物販注文) - mua sản phẩm thông thường
- Vòng đời: New → Paid → Shipped → Delivered (không thể bỏ qua trạng thái)
- Ví dụ: Người dùng quyên góp ¥10,000 cho Kyoto City và nhận một chai sake

3. Products (Sản phẩm)
- Sản phẩm được cung cấp làm quà cảm ơn cho quyên góp hoặc bán trong cửa hàng
- Quản lý bởi: Producers (nhà sản xuất / 生産者)
- Tính năng: Danh mục, thông số kỹ thuật, tồn kho, giá cả
- Ví dụ: "Kyoto Premium Sake 720ml" - sản phẩm được cung cấp bởi nhà sản xuất

4. Vending Machines (Máy bán hàng / 自販機)
- Máy vật lý bán sản phẩm và tạo đơn hàng tự động
- Mục đích: Cho phép bán hàng trực tiếp tại địa điểm vật lý
- Tích hợp: Máy giao tiếp với hệ thống qua API để tạo đơn hàng
- Ví dụ: Máy bán hàng tại ga tàu bán sản phẩm địa phương

5. Coins (Xu / Điểm thưởng)
- Hệ thống điểm thưởng với hai loại:
  - Common Coins: Có thể dùng ở tất cả coin shops trong một cửa hàng
  - Unique Coins: Dành riêng cho một số nhóm coin shop cụ thể
- Kiếm xu: Người dùng nhận xu khi mua hàng hoặc quyên góp
- Tiêu xu: Xu có thể dùng để mua sản phẩm từ coin shops
- Hết hạn: Xu có ngày hết hạn dựa trên cấu hình cửa hàng
- Ví dụ: Người dùng kiếm 100 xu từ quyên góp, có thể dùng sau để mua sản phẩm

6. Deals (Giao dịch / 取引)
- Thỏa thuận tài chính định nghĩa cách tiền chảy giữa các groups
- Các bên: Receiving Group (nhóm nhận thanh toán, ví dụ: nhà sản xuất), Paying Group (nhóm thanh toán, ví dụ: đô thị)
- Loại: Tỷ lệ doanh thu hàng tháng, số tiền cố định hàng tháng, giá bán buôn, số tiền cố định mỗi đơn, chuyển đổi xu, và nhiều loại khác
- Mục đích: Tự động tính toán mỗi bên nên nhận/trả bao nhiêu dựa trên doanh số
- Ví dụ: Deal nơi nhà sản xuất nhận 70% doanh số từ sản phẩm của họ bán trong cửa hàng của đô thị

7. Invoices (Hóa đơn)
- Hóa đơn được tạo dựa trên deals và dữ liệu đơn hàng thực tế
- Mục đích: Tính toán và ghi lại giao dịch tài chính giữa các groups
- Tạo: Được tạo hàng tháng hoặc mỗi đơn dựa trên loại deal
- Ví dụ: Hóa đơn hàng tháng cho thấy nhà sản xuất nên nhận ¥500,000 dựa trên deal với đô thị

8. Groups (Tổ chức / 組織)
- Tổ chức tham gia hệ thống
- Loại: Đô thị (市町村), Nhà sản xuất (生産者), Đại lý (仲介者), Affiliaters (アフィリエイター), Brokers (仲介業者)
- Mục đích: Đại diện cho các bên khác nhau tham gia hệ sinh thái quyên góp

9. Admins (Quản trị viên / 管理者)
- Quản trị viên hệ thống với các vai trò và quyền khác nhau
- Vai trò: Quản trị cửa hàng/trang, Quản trị thuế, Nhà sản xuất, Người giao hàng, Affiliaters, Nhân viên bán hàng
- Mục đích: Quản lý cửa hàng, sản phẩm, đơn hàng và cấu hình hệ thống
- Quyền: Dựa trên vai trò, không phải tất cả admin đều có thể truy cập tất cả tính năng

10. Users (Người dùng / 利用者)
- Khách hàng cuối thực hiện quyên góp và mua hàng
- Tính năng: Quản lý tài khoản, lịch sử đơn hàng, số dư xu, quản lý địa chỉ
- Ví dụ: Một công dân quyên góp cho nhiều đô thị trong năm

────────────────────────────────

CÁCH CÁC THỰC THỂ TƯƠNG TÁC

────────────────────────────────

Luồng quyên góp điển hình:
1. Người dùng duyệt cửa hàng của đô thị (trang quyên góp thuế)
2. Người dùng chọn sản phẩm muốn làm quà cảm ơn
3. Người dùng đặt đơn (yêu cầu quyên góp) với thanh toán
4. Đơn hàng được tạo trong hệ thống với trạng thái "New"
5. Thanh toán được xử lý (qua GMO, Paygent hoặc cổng thanh toán khác)
6. Trạng thái đơn hàng chuyển sang "Paid" sau khi xác nhận thanh toán
7. Nhà sản xuất giao sản phẩm
8. Trạng thái đơn hàng chuyển sang "Shipped"
9. Người dùng nhận sản phẩm
10. Deals được tính toán dựa trên đơn hàng
11. Invoices được tạo cho các groups liên quan

Luồng máy bán hàng:
1. Khách hàng sử dụng máy bán hàng vật lý
2. Máy gửi dữ liệu đơn hàng đến hệ thống qua API
3. Hệ thống tạo đơn hàng tự động (có thể tạo tài khoản người dùng nếu cần)
4. Đơn hàng theo vòng đời giống như đơn trực tuyến
5. Deals và invoices được tính toán tương tự

Luồng hệ thống xu:
1. Người dùng thực hiện mua hàng hoặc quyên góp
2. Người dùng kiếm xu dựa trên cấu hình cửa hàng
3. Xu được lưu trong tài khoản người dùng (common hoặc unique coins)
4. Người dùng duyệt coin shops
5. Người dùng tiêu xu để mua sản phẩm
6. Xu hết hạn sau một khoảng thời gian (nếu được cấu hình)

Luồng Deal và Invoice:
1. Admin tạo deal giữa hai groups (ví dụ: nhà sản xuất và đô thị)
2. Deal định nghĩa điều khoản thanh toán (tỷ lệ, số tiền cố định, v.v.)
3. Đơn hàng được đặt và hoàn thành
4. Hệ thống tính toán số tiền deal dựa trên dữ liệu đơn hàng
5. Invoices được tạo hàng tháng hoặc mỗi đơn
6. Groups nhận/trả theo số tiền invoice

────────────────────────────────

HẠN CHẾ VÀ QUY TẮC QUAN TRỌNG

────────────────────────────────

Hạn chế ECSite (Frontend):
- Không có chức năng tìm kiếm sản phẩm: Người dùng không thể tìm kiếm sản phẩm theo từ khóa, danh mục trên ECSite
- Không có trang danh sách/lọc sản phẩm: Không có trang danh sách sản phẩm với tùy chọn lọc (khoảng giá, nhà sản xuất, thể loại, v.v.)
- Không có tùy chọn sắp xếp sản phẩm cho người dùng: Người dùng cuối không thể sắp xếp sản phẩm trên frontend
- Không có đánh giá/xếp hạng khách hàng: Mặc dù có bảng reviews trong database, đánh giá không được hiển thị trên frontend
- Không có wishlist/favorites: Người dùng không thể lưu sản phẩm vào danh sách yêu thích
- Không có video sản phẩm: Chỉ hỗ trợ hình ảnh
- Không có thông báo hết hàng: Người dùng không thể đăng ký nhận thông báo khi sản phẩm hết hàng có lại
- Không hỗ trợ đa ngôn ngữ trên frontend: Mặc dù có thư mục ngôn ngữ, frontend không hỗ trợ chuyển đổi ngôn ngữ

Hạn chế trạng thái đơn hàng:
- Đơn hàng tuân theo chuyển đổi trạng thái nghiêm ngặt: New → Paid → Shipped → Delivered
- Không thể bỏ qua trạng thái (ví dụ: không thể đi từ New trực tiếp đến Shipped)
- Thay đổi trạng thái phải tuân theo chuyển đổi hợp lệ (được định nghĩa trong shipment_status_maps)

Hạn chế loại cửa hàng:
- Trang quyên góp thuế: Chủ yếu để nhận quyên góp được khấu trừ thuế
- Cửa hàng thông thường: Cho bán hàng thương mại điện tử tiêu chuẩn
- Loại cửa hàng ảnh hưởng đến xử lý đơn hàng, tính toán thuế và tính năng có sẵn

Hạn chế loại Deal:
- Mỗi loại deal có quy tắc tính toán cụ thể
- Deals có ngày bắt đầu và kết thúc
- Deals có thể được gắn với máy bán hàng cụ thể (cho deals doanh số hàng tháng)
- Phạm vi giá trị deal có thể áp dụng (giá theo tầng dựa trên khối lượng bán hàng)

Hạn chế thanh toán:
- Phương thức thanh toán được định nghĩa trước (thẻ tín dụng, chuyển khoản ngân hàng, v.v.)
- Xử lý thanh toán được xử lý bởi cổng bên ngoài (GMO, Paygent)
- Một số phương thức thanh toán có thể không có sẵn cho tất cả loại cửa hàng

Hạn chế sản phẩm và tồn kho:
- Sản phẩm phải thuộc về một nhà sản xuất
- Tồn kho được theo dõi theo thông số kỹ thuật sản phẩm
- Sản phẩm hết hàng không thể đặt hàng
- Sản phẩm có thể được gán cho máy bán hàng cụ thể

Hạn chế tài khoản người dùng:
- Thử đăng nhập: Tài khoản bị khóa sau 3 lần đăng nhập thất bại
- Thời gian khóa: 300 giây (5 phút)
- Yêu cầu mật khẩu: Phải chứa chữ hoa, chữ thường, số và từ 8-32 ký tự
- Xác minh email: Bắt buộc để tạo tài khoản

Quy tắc tính toán tài chính:
- Tính toán deals dựa trên dữ liệu đơn hàng thực tế
- Tạo invoice xảy ra hàng tháng hoặc mỗi đơn dựa trên loại deal
- Phân phối thanh toán tuân theo thỏa thuận deals giữa groups
- Xử lý thuế thay đổi theo loại sản phẩm và cấu hình deal

Quy tắc xử lý đơn hàng:
- Đơn hàng không thể chỉnh sửa sau khi thanh toán
- Thay đổi trạng thái đơn hàng phải là chuyển đổi hợp lệ
- Ngày giao hàng được ghi lại khi trạng thái chuyển sang "Shipped"
- Ngày thanh toán được ghi lại khi trạng thái chuyển sang "Paid"

Quy tắc quản lý xu:
- Xu được kiếm tại thời điểm mua/quyên góp
- Xu hết hạn dựa trên cấu hình cửa hàng
- Sử dụng xu không được vượt quá số dư có sẵn
- Tỷ lệ xu có thể thay đổi theo nhóm coin shop

Quy tắc quản lý sản phẩm:
- Sản phẩm phải có liên kết nhà sản xuất hợp lệ
- Tồn kho phải đủ cho đơn hàng
- Sản phẩm có thể được gán cho danh mục
- Sản phẩm có thể được liên kết với máy bán hàng cụ thể

────────────────────────────────

KỊCH BẢN THƯỜNG GẶP

────────────────────────────────

Kịch bản 1: Người dùng thực hiện quyên góp
1. Người dùng truy cập trang quyên góp thuế của Kyoto City
2. Người dùng chọn "Premium Sake Set" (¥10,000)
3. Người dùng hoàn tất thanh toán qua thẻ tín dụng
4. Đơn hàng được tạo với trạng thái "New"
5. Thanh toán được xác nhận, trạng thái chuyển sang "Paid"
6. Nhà sản xuất giao sake, trạng thái chuyển sang "Shipped"
7. Người dùng nhận sản phẩm
8. Hệ thống tính toán deal: Nhà sản xuất nhận 70% (¥7,000), Đô thị giữ 30% (¥3,000)
9. Invoice được tạo cho nhà sản xuất

Kịch bản 2: Bán hàng qua máy bán hàng
1. Khách hàng đến máy bán hàng tại ga tàu
2. Khách hàng chọn sản phẩm và thanh toán
3. Máy gửi dữ liệu đơn hàng đến UNIOSS3 API
4. Hệ thống tạo đơn hàng và tài khoản người dùng (nếu cần)
5. Đơn hàng theo luồng xử lý bình thường
6. Tính toán deals và invoices được tạo

Kịch bản 3: Sử dụng xu
1. Người dùng có 500 common coins từ quyên góp trước
2. Người dùng duyệt coin shops trong cửa hàng
3. Người dùng tìm sản phẩm có giá 300 xu
4. Người dùng mua sản phẩm bằng xu
5. Số dư xu của người dùng giảm xuống 200 xu
6. Sản phẩm được giao bình thường

────────────────────────────────

LƯU Ý KHI PHÂN TÍCH TICKET

────────────────────────────────

Khi phân tích ticket liên quan đến UNIOSS3, hãy xem xét:
- Trạng thái refactoring hiện tại (admin_id migration)
- Quy tắc kinh doanh xung quanh đơn hàng, deals và invoices
- Luồng trải nghiệm người dùng (quyên góp → sản phẩm → xu)
- Quyền và hạn chế vai trò quản trị
- Tính toàn vẹn dữ liệu và an toàn giao dịch
- Hạn chế của ECSite frontend so với các nền tảng thương mại điện tử lớn
- Quy tắc chuyển đổi trạng thái đơn hàng nghiêm ngặt
- Tính phức tạp của tính toán deals và invoices

────────────────────────────────

1. THÔNG TIN ĐẦU VÀO (TICKET DATA)

────────────────────────────────



=== THÔNG TIN TICKET ===

Tiêu đề: {title}

Mô tả: {description}

Trạng thái: {state}

Độ ưu tiên: {priority}

Nhãn: {labels}

Người được giao: {assignee}

Người tạo: {author}

Ngày tạo: {created_at}

Ngày cập nhật: {updated_at}

Milestone: {milestone}

URL: {url}



=== COMMENTS ({comment_count} tổng cộng) ===

{comments}



=== RELATED ISSUES ===

{related_issues}



=== ATTACHMENTS & IMAGES ===

{attachments}



────────────────────────────────

2. VAI TRÒ & MỤC TIÊU

────────────────────────────────



Bạn là một chuyên gia phân tích và triển khai dự án phần mềm, đang làm việc với dự án phần mềm cho khách hàng Nhật.



Mục tiêu:

- Hiểu đúng và sâu yêu cầu của ticket

- Tránh hiểu nhầm với khách hàng

- Giúp toàn bộ team (Dev / QA / PM) có cùng nhận thức

- Biến yêu cầu thành hành động cụ thể, khả thi và kiểm chứng được



────────────────────────────────

3. KHUNG TƯ DUY PHÂN TÍCH (WWWH-TR)

────────────────────────────────



Phân tích theo từng phần sau:



- W1 — Why

  Tại sao phải làm điều này?

  → Làm rõ vấn đề gốc rễ và mục tiêu cuối cùng.



- W2 — What

  Cụ thể cần làm những gì?

  → Xác định yêu cầu, phạm vi và thông tin liên quan.



- W3 — Who

  Ai liên quan / ai bị ảnh hưởng?

  → Xác định stakeholder, người ra quyết định và người hỗ trợ.



- H — How

  Có những cách nào để thực hiện?

  → Đề xuất các phương án khả thi, so sánh ưu / nhược điểm và sự đánh đổi.



- T — Test

  Kiểm chứng thế nào?

  → Đề xuất thử nghiệm nhỏ, tiêu chí đo lường (thời gian, chi phí, chất lượng, rủi ro).



- R — Reflect

  Giải pháp tối ưu là gì?

  → Đánh giá, kết luận, bước tiếp theo và điều chỉnh cần thiết.



────────────────────────────────

4. YÊU CẦU NỘI DUNG BẮT BUỘC

────────────────────────────────



Trong phân tích, bắt buộc phải làm rõ:



1. Mong muốn thực sự của khách hàng (kể cả yêu cầu ẩn).

2. Các điểm chưa rõ, mâu thuẫn hoặc cần xác nhận lại với khách hàng.

3. Definition of Done cụ thể cho từng tính năng hoặc giai đoạn.

4. Các hành động cụ thể cần thực hiện để đáp ứng yêu cầu và tiến độ.

5. Phương pháp kiểm thử phù hợp để đảm bảo chất lượng sản phẩm.

6. Trình bày rõ ràng, dễ hiểu để cả team và khách hàng cùng nắm bắt.

7. Ước lượng (Estimation): Phải đưa ra ước lượng Story Points cho ticket này.
   - Sử dụng dãy số Fibonacci: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89
   - Quy ước: 8 Story Points = 1 tuần làm việc
   - Xem xét độ phức tạp, rủi ro, và phạm vi công việc để đưa ra ước lượng chính xác



────────────────────────────────

5. HƯỚNG DẪN TRÌNH BÀY

────────────────────────────────



⚠️ YÊU CẦU NGÔN NGỮ BẮT BUỘC:

- TẤT CẢ nội dung phân tích PHẢI được viết bằng TIẾNG VIỆT
- Các phần TL;DR, Action Items, Open Questions, W1-W3, H, T, R PHẢI hoàn toàn bằng tiếng Việt
- Ngôn ngữ đơn giản, rõ ràng, chính xác
- Tránh thuật ngữ phức tạp không cần thiết
- Thuật ngữ kỹ thuật có thể giữ tiếng Anh / tiếng Nhật khi phù hợp (ví dụ: API, database, 納税サイト)
- Nhấn mạnh các điểm quan trọng, rủi ro và quyết định



────────────────────────────────

6. OUTPUT REQUIREMENTS (FIXED HTML TEMPLATE – BẮT BUỘC)

────────────────────────────────



⚠️ QUAN TRỌNG NHẤT:

Bạn PHẢI sử dụng template HTML cố định được cung cấp bên dưới và ĐIỀN ĐẦY ĐỦ tất cả các placeholder bằng nội dung phân tích của bạn.

KHÔNG được tạo HTML mới, KHÔNG được thay đổi cấu trúc template.

CHỈ được thay thế các placeholder sau bằng nội dung thực tế:

- {{ESTIMATION}}: Ước lượng Story Points (ví dụ: "3 Story Points (~ 2 ngày), 5 Story Points (~ 3 ngày), 8 Story Points (~ 1 tuần)")
- {{TLDR_ITEMS}}: Danh sách <li> cho TL;DR (>5 bullet points)
- {{ACTION_ITEMS}}: Danh sách <li> cho Action Items
- {{OPEN_QUESTIONS}}: Danh sách <li> cho Open Questions (hoặc "Không có câu hỏi cần xác nhận")
- {{W1_ITEMS}}: Danh sách <li> cho W1 — Why
- {{W2_ITEMS}}: Danh sách <li> cho W2 — What
- {{W3_ITEMS}}: Danh sách <li> cho W3 — Who
- {{H_ITEMS}}: Danh sách <li> cho H — How
- {{T_ITEMS}}: Danh sách <li> cho T — Test
- {{R_ITEMS}}: Danh sách <li> cho R — Reflect



6.1. Yêu cầu điền template:

- Mỗi placeholder PHẢI được thay thế bằng nội dung thực tế
- Đối với {{ESTIMATION}}: Điền Story Points theo dãy Fibonacci (1, 2, 3, 5, 8, 13, 21, 34, 55, 89) và quy đổi sang ngày hoặc 1 tuần (8 points = 1 tuần). Ví dụ: 3 Story Points (~ 2 ngày), 5 Story Points (~ 4 ngày), 8 Story Points (~ 1 tuầntuần)"
- Đối với các placeholder khác: PHẢI được thay thế bằng danh sách <li>...</li> hợp lệ
- Mỗi <li> phải chứa nội dung phân tích cụ thể, không được để trống
- Nếu một section không có nội dung, vẫn phải có ít nhất 1 <li> với nội dung "Chưa có nội dung" hoặc tương tự
- TẤT CẢ nội dung trong <li> phải được escape HTML đúng cách (không chứa HTML không hợp lệ)
- KHÔNG được thêm bất kỳ tag HTML nào ngoài <li> trong các placeholder



6.2. Format output:

Output PHẢI nằm giữa hai marker sau:

<!-- AI_EMAIL_HTML_START -->

[Template HTML đã được điền đầy đủ]

<!-- AI_EMAIL_HTML_END -->



KHÔNG kèm bất kỳ giải thích nào ngoài HTML giữa hai marker này."""


class IssueAnalyzer:
    """
    Analyzer for GitLab issues using AI providers.

    Supports OpenRouter (recommended) and OpenAI with OpenAI-compatible API interface.
    """

    PROVIDERS = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer",
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer",
        },
    }

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 120,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        enable_reasoning: bool = False,
    ):
        """
        Initialize issue analyzer.

        Args:
            provider: AI provider ('openrouter', 'openai')
            api_key: API key for the provider
            model: Model name to use (e.g., 'tngtech/deepseek-r1t2-chimera:free' for OpenRouter)
            base_url: Optional custom base URL (overrides provider default)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff: Exponential backoff multiplier
            enable_reasoning: Enable reasoning/deepthink mode (for OpenRouter with DeepSeek)
        """
        if provider not in self.PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: {', '.join(self.PROVIDERS.keys())}"
            )

        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.enable_reasoning = enable_reasoning

        # Get provider configuration
        provider_config = self.PROVIDERS[provider].copy()

        # Use custom base_url if provided, otherwise use provider default
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif provider_config["base_url"]:
            self.base_url = provider_config["base_url"]
        else:
            raise ValueError(f"base_url must be provided for provider '{provider}'")

        # Build authentication headers
        auth_header = provider_config["auth_header"]
        auth_prefix = provider_config["auth_prefix"]

        auth_value = f"{auth_prefix} {api_key}"
        self.headers = {auth_header: auth_value, "Content-Type": "application/json"}

    def analyze_issue(
        self, issue_data: Dict[str, Any], gitlab_url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Analyze issue using AI and return WWWH-TR structured analysis.

        Args:
            issue_data: Comprehensive issue data dictionary

        Returns:
            Dictionary with WWWH-TR sections:
            - 'W1': Why section
            - 'W2': What section
            - 'W3': Who section
            - 'H': How section
            - 'T': Test section
            - 'R': Reflect section

        Raises:
            AnalysisError: If analysis fails
            ValueError: If issue_data is empty or invalid
        """
        if not issue_data:
            raise ValueError("issue_data cannot be empty")

        # Prepare prompt
        logger.info("👉 Preparing prompt for AI analysis...")
        prompt = self.prepare_prompt(issue_data, gitlab_url=gitlab_url)

        # Call AI API
        logger.info("👉 Calling to AI chat completion via API...")
        response = self.call_ai_api(prompt)

        # Parse response
        analysis = self.parse_analysis(response)

        return analysis

    def prepare_prompt(
        self, issue_data: Dict[str, Any], gitlab_url: Optional[str] = None
    ) -> str:
        """
        Format comprehensive issue data into analysis prompt.

        Args:
            issue_data: Comprehensive issue data dictionary
            gitlab_url: Optional GitLab instance URL for converting relative image URLs

        Returns:
            Formatted prompt string
        """
        # Get GitLab URL from issue_data if not provided
        if not gitlab_url:
            # Try to extract from web_url
            web_url = issue_data.get("web_url") or issue_data.get("url", "")
            if web_url:
                from urllib.parse import urlparse

                parsed = urlparse(web_url)
                gitlab_url = f"{parsed.scheme}://{parsed.netloc}"

        # Get project_id from issue_data
        project_id = issue_data.get("project_id")

        # Format description with converted image URLs
        description = issue_data.get("description", "")
        if description and gitlab_url:
            description = convert_relative_image_urls(
                description, gitlab_url, project_id
            )

        # Format comments
        comments_text = "Không có comments"
        if issue_data.get("comments"):
            comments_list = []
            for comment in issue_data["comments"]:
                if not comment.get("system", False):  # Skip system notes
                    author = comment.get("author", {})
                    if isinstance(author, dict):
                        author_name = author.get(
                            "username", author.get("name", "Unknown")
                        )
                    else:
                        author_name = "Unknown"

                    body = comment.get("body", "")
                    # Convert relative image URLs in comments too
                    if body and gitlab_url:
                        body = convert_relative_image_urls(body, gitlab_url, project_id)
                    created = comment.get("created_at", "")
                    comments_list.append(f"[{author_name} @ {created}]: {body}")

            comments_text = (
                "\n".join(comments_list) if comments_list else "Không có comments"
            )

        # Format related issues
        related_text = "Không có related issues"
        if issue_data.get("related_issues"):
            related_list = []
            for related in issue_data["related_issues"]:
                if isinstance(related, dict):
                    iid = related.get("iid", related.get("id", "?"))
                    title = related.get("title", "Unknown")
                    link_type = related.get("link_type", "related")
                    related_list.append(f"- #{iid}: {title} ({link_type})")
            related_text = (
                "\n".join(related_list) if related_list else "Không có related issues"
            )

        # Format attachments
        attachments_text = "Không có attachments"
        if issue_data.get("attachments"):
            attachments_list = []
            for att in issue_data["attachments"]:
                url = att.get("url", "")
                source = att.get("source", "unknown")
                attachments_list.append(f"- {url} (từ {source})")
            attachments_text = (
                "\n".join(attachments_list)
                if attachments_list
                else "Không có attachments"
            )

        # Format labels
        labels = issue_data.get("labels", [])
        if labels:
            labels_str = ", ".join(
                [
                    label.get("name", label) if isinstance(label, dict) else str(label)
                    for label in labels
                ]
            )
        else:
            labels_str = "Không có"

        # Format assignee
        assignee = issue_data.get("assignee")
        if isinstance(assignee, dict):
            assignee_str = assignee.get("username", assignee.get("name", "Unassigned"))
        elif assignee:
            assignee_str = str(assignee)
        else:
            assignee_str = "Chưa được giao"

        # Format author
        author = issue_data.get("author")
        if isinstance(author, dict):
            author_str = author.get("username", author.get("name", "Unknown"))
        elif author:
            author_str = str(author)
        else:
            author_str = "Unknown"

        # Format milestone
        milestone = issue_data.get("milestone")
        if isinstance(milestone, dict):
            milestone_str = milestone.get("title", "None")
        elif milestone:
            milestone_str = str(milestone)
        else:
            milestone_str = "Không có"

        # Count comments
        comment_count = issue_data.get(
            "comment_count", len(issue_data.get("comments", []))
        )

        # Format the main prompt
        main_prompt = USER_PROMPT_TEMPLATE.format(
            title=issue_data.get("title", ""),
            description=description,
            state=issue_data.get("state", "unknown"),
            priority=issue_data.get("priority", "not set"),
            labels=labels_str,
            assignee=assignee_str,
            author=author_str,
            created_at=issue_data.get("created_at", ""),
            updated_at=issue_data.get("updated_at", ""),
            milestone=milestone_str,
            url=issue_data.get("web_url", issue_data.get("url", "")),
            comment_count=comment_count,
            comments=comments_text,
            related_issues=related_text,
            attachments=attachments_text,
        )

        # Get the fixed HTML template with issue metadata filled
        html_template = get_fixed_html_template(issue_data)

        # Append the fixed HTML template to the prompt
        full_prompt = f"""{main_prompt}


────────────────────────────────

7. HTML TEMPLATE (BẮT BUỘC PHẢI SỬ DỤNG)

────────────────────────────────

⚠️ BẠN PHẢI SỬ DỤNG TEMPLATE SAU ĐÂY:

Điền tất cả các placeholder {{TLDR_ITEMS}}, {{ACTION_ITEMS}}, {{OPEN_QUESTIONS}}, {{W1_ITEMS}}, {{W2_ITEMS}}, {{W3_ITEMS}}, {{H_ITEMS}}, {{T_ITEMS}}, {{R_ITEMS}} bằng nội dung phân tích của bạn.

KHÔNG được thay đổi cấu trúc HTML, KHÔNG được thêm/bớt tag nào.

CHỈ được thay thế các placeholder bằng danh sách <li>...</li> hợp lệ.


{html_template}


────────────────────────────────

NHẮC LẠI YÊU CẦU:

1. Phân tích ticket theo WWWH-TR framework
2. Điền đầy đủ tất cả placeholder trong template HTML trên
3. Output HTML đã điền phải nằm giữa <!-- AI_EMAIL_HTML_START --> và <!-- AI_EMAIL_HTML_END -->
4. KHÔNG kèm giải thích ngoài HTML
"""

        return full_prompt

    def call_ai_api(self, prompt: str) -> Dict[str, Any]:
        """
        Make API request to AI provider.

        Args:
            prompt: Formatted prompt string

        Returns:
            API response dictionary

        Raises:
            AnalysisError: If API request fails
        """
        url = f"{self.base_url}/chat/completions"

        # For reasoning mode, increase max_tokens to ensure complete responses
        # Reasoning mode can produce very long outputs, so we need more tokens
        effective_max_tokens = self.max_tokens
        if self.enable_reasoning:
            # Increase max_tokens for reasoning mode to handle longer outputs
            # Default is 2000, but reasoning mode may need 8000-16000 for complete HTML
            effective_max_tokens = max(self.max_tokens, 16000)
            logger.info("👉 Reasoning mode enabled, using max_tokens=16000")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": effective_max_tokens,
            "stream": False,
        }

        # Add reasoning/deepthink mode for OpenRouter
        if self.enable_reasoning and self.provider == "openrouter":
            payload["reasoning"] = {"enabled": True}

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"👉 AI API request attempt {attempt + 1}/{self.max_retries} to {url}"
                )
                response = requests.post(
                    url, headers=self.headers, json=payload, timeout=self.timeout
                )
                response.raise_for_status()
                response_data = response.json()
                logger.info(
                    f"✅ AI API request successful, response keys: {list(response_data.keys())}"
                )
                
                # Log token usage if available
                if "usage" in response_data:
                    usage = response_data["usage"]
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    logger.info(
                        f"✅ Token usage: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}"
                    )
                
                return response_data

            except Timeout as e:
                if attempt == self.max_retries - 1:
                    raise AnalysisError(
                        f"AI API request timeout after {self.max_retries} attempts: {e}",
                        timeout=True,
                    )
                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

            except HTTPError as e:
                status_code = e.response.status_code if e.response else None

                # Don't retry on client errors (4xx), except 429 (rate limit)
                if status_code and 400 <= status_code < 500 and status_code != 429:
                    error_msg = f"AI API error: {e}"
                    if status_code == 401:
                        error_msg = "AI API authentication failed. Check your API key."
                    raise AnalysisError(error_msg, status_code=status_code)

                # Retry on server errors (5xx) and rate limits (429)
                if attempt == self.max_retries - 1:
                    raise AnalysisError(
                        f"AI API error after {self.max_retries} attempts: {e}",
                        status_code=status_code,
                    )

                if status_code == 429:
                    # Rate limited - check Retry-After header and wait
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    if attempt == self.max_retries - 1:
                        raise AnalysisError(
                            f"AI API rate limit exceeded. Retry after {retry_after} seconds.",
                            status_code=429,
                            retry_after=retry_after,
                        )
                    logger.warning(
                        f"Rate limited, waiting {retry_after} seconds before retry..."
                    )
                    time.sleep(retry_after)
                    continue

                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

            except RequestException as e:
                if attempt == self.max_retries - 1:
                    raise AnalysisError(f"Network error: {e}")
                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

        raise AnalysisError("AI API request failed after all retries")

    def parse_analysis(self, response: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse AI API response and extract WWWH-TR sections.

        Args:
            response: API response dictionary

        Returns:
            Dictionary with WWWH-TR sections (W1, W2, W3, H, T, R)

        Raises:
            AnalysisError: If response cannot be parsed
        """
        # Extract content from OpenAI-compatible response (OpenRouter, OpenAI)
        content = None

        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            message = choice.get("message", {})

            # Get content from message (handle None explicitly)
            content = message.get("content")

            # Handle None or empty string
            if content is None:
                content = ""

            # If content is empty, check for alternative locations
            if not content:
                finish_reason = choice.get("finish_reason")
                logger.warning(
                    f"Content is empty. finish_reason: {finish_reason}, message keys: {list(message.keys())}"
                )

                # Check if there's a reasoning field in message
                if "reasoning" in message:
                    reasoning_val = message.get("reasoning")
                    if reasoning_val:
                        content = str(reasoning_val)

                # Check if content is in a different location (e.g., direct in choice)
                if not content and "content" in choice:
                    content = choice.get("content")

                # If still empty, try to find any string content in message as fallback
                if not content:
                    for key, value in message.items():
                        if (
                            isinstance(value, str) and len(value) > 50
                        ):  # Reasonable content length
                            content = value
                            break

                # If still empty, this is likely an API issue
                if not content:
                    raise AnalysisError(
                        f"Unable to extract content from AI API response. "
                        f"Response has 'choices' but content is empty. "
                        f"finish_reason: {finish_reason}, message keys: {list(message.keys())}"
                    )
        elif "text" in response:
            content = response["text"]
        else:
            raise AnalysisError(
                f"Unable to extract content from AI API response. Response keys: {list(response.keys())}"
            )

        if not content:
            raise AnalysisError(
                f"Content is empty after extraction. Response structure: {response}"
            )

        # Check if response was truncated (finish_reason == "length")
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            finish_reason = choice.get("finish_reason")
            if finish_reason == "length":
                logger.warning(
                    f"AI response was truncated due to max_tokens limit! "
                    f"Content length: {len(content)}. "
                    f"Consider increasing max_tokens (current: {self.max_tokens})."
                )

        # Extract HTML from content (between markers)
        logger.info("👉 Prepare HTML template from AI response...")
        html_content = self._extract_html_from_content(content)

        # Validate that HTML is complete (has end marker)
        if html_content and "<!-- AI_EMAIL_HTML_END -->" not in content:
            logger.warning(
                f"HTML end marker not found in response! "
                f"This indicates the AI response was incomplete. "
                f"HTML length: {len(html_content)}, Raw content length: {len(content)}. "
                f"Consider increasing max_tokens (current: {self.max_tokens})."
            )

        if html_content:
            logger.info("✅ HTML template is available")

        return {"html": html_content, "raw": content}

    def _extract_html_from_content(self, content: str) -> str:
        """
        Extract HTML content from AI response between markers.

        Args:
            content: AI response text containing HTML between markers

        Returns:
            Extracted HTML string, or fallback if markers not found
        """
        # Look for HTML between markers
        start_marker = "<!-- AI_EMAIL_HTML_START -->"
        end_marker = "<!-- AI_EMAIL_HTML_END -->"

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            # Extract HTML between markers
            html = content[start_idx + len(start_marker) : end_idx].strip()
            return html
        elif start_idx != -1 and end_idx == -1:
            # Start marker found but end marker missing - response might be truncated
            logger.warning(
                f"HTML start marker found but end marker missing! "
                f"This indicates the AI response was truncated. "
                f"Content length: {len(content)}, Start position: {start_idx}"
            )
            # Extract from start marker to end of content, but log warning
            html = content[start_idx + len(start_marker) :].strip()
            logger.warning(
                f"Extracted incomplete HTML (length: {len(html)}). "
                f"Consider increasing max_tokens or checking AI response limits."
            )
            return html
        else:
            # Fallback: try to find HTML tags in content
            # Look for any HTML-like content
            if "<table" in content or "<div" in content or "<p" in content:
                # Try to extract HTML block
                html_start = content.find("<")
                html_end = content.rfind(">")
                if html_start != -1 and html_end != -1 and html_end > html_start:
                    html = content[html_start : html_end + 1].strip()
                    return html

            # Last resort: return empty and let reporter handle fallback
            return ""
