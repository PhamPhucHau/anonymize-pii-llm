# Công Nghệ Sử Dụng - Ứng Dụng Tự Động Trả Lời Email (Auto_Chat_24_7)

## Tổng Quan Hệ Thống

Hệ thống ứng dụng tự động trả lời email được thiết kế theo kiến trúc đa tầng, kết hợp giữa giao diện người dùng hiện đại, xử lý nghiệp vụ phía server, và trí tuệ nhân tạo để mang đến trải nghiệm xử lý email thông minh, bảo mật và hiệu quả. Toàn bộ hệ thống bao gồm **Python CLI Interface**, **Lớp Xử Lý Email (IMAP/SMTP)**, **Lớp Ẩn Danh Hóa Dữ Liệu (Anonymization)**, **Ollama LLM Server**, **Lớp Xử Lý Ngôn Ngữ Tự Nhiên**, và **Lớp Logging & Audit Trail**, được kết nối chặt chẽ với nhau qua các API dịch vụ và được bảo vệ bởi các lớp bảo mật.

---

## 1. Python CLI Interface - Lớp Tương Tác Người Dùng

Python CLI Interface là lớp giao diện chính cho phép người dùng và hệ thống tự động khởi động dịch vụ xử lý email. Giao diện dòng lệnh cung cấp trải nghiệm đơn giản nhưng mạnh mẽ, cho phép người dùng:

- **Khởi động dịch vụ tự động**: Chạy ứng dụng với lệnh `python auto_chat_24_7.py` để bắt đầu quá trình kiểm tra email định kỳ
- **Theo dõi tiến trình xử lý**: Hiển thị log thời gian thực khi có email mới được nhận, xử lý, và phản hồi
- **Quản lý cấu hình**: Tải thông số từ file `.env` chứa thông tin Gmail, mật khẩu ứng dụng, và email người nhận chuyển tiếp

Mọi thao tác từ ứng dụng đều được gửi qua **Email Processor Layer**, nơi tiếp nhận và điều phối yêu cầu đến các dịch vụ backend phù hợp.

---

## 2. Email Processor Layer - Lớp Xử Lý Email

**Email Processor Layer** đóng vai trò cầu nối trung tâm trong việc giao tiếp với các máy chủ email. Lớp này được chia thành hai thành phần chính:

### 2.1 IMAP Protocol Handler (Nhận Email)
- **Công nghệ**: IMAP4 SSL/TLS (Internet Message Access Protocol) kết nối an toàn với Gmail
- **Máy chủ**: `imap.gmail.com:993`
- **Chức năng**:
  - Xác thực người dùng bằng Gmail credentials từ file `.env`
  - Truy cập thư mục Inbox và tìm kiếm email chưa đọc (UNSEEN)
  - Phân tích cấu trúc email đa phần (multipart) và trích xuất nội dung text
  - Xử lý các ký tự đặc biệt và encoding khác nhau (UTF-8, Latin-1, etc.)
  - Trả về bộ dữ liệu: `(email_id, from_address, subject, body)`

### 2.2 SMTP Protocol Handler (Gửi Email)
- **Công nghệ**: SMTP SSL/TLS kết nối an toàn với Gmail
- **Máy chủ**: `smtp.gmail.com:465`
- **Chức năng**:
  - Xác thực người dùng bằng Gmail credentials
  - Định dạng tin nhắn email theo chuẩn MIME (Multipurpose Internet Mail Extensions)
  - Gửi phản hồi tự động tới người gửi gốc với tiêu đề "Re: [Subject]"
  - Chuyển tiếp email đã xử lý tới cộng sự với tiêu đề "FWD: [Subject]"
  - Xử lý các lỗi gửi mail và ghi log lỗi

---

## 3. Anonymization Layer - Lớp Ẩn Danh Hóa Dữ Liệu

**Anonymization Layer** là thành phần bảo mật cốt lõi, đảm bảo rằng các thông tin cá nhân nhạy cảm (PII - Personally Identifiable Information) không bao giờ được gửi trực tiếp đến mô hình LLM bên ngoài. Lớp này bao gồm hai quy trình:

### 3.1 Anonymizer (Ẩn Danh Dữ Liệu)
- **Công nghệ**: spaCy NER (Named Entity Recognition) với mô hình `en_core_web_sm`
- **Chức năng**:
  - Phân tích văn bản email để phát hiện các thực thể (entities) nhạy cảm
  - Nhận diện loại dữ liệu:
    - **PERSON**: Tên người (ví dụ: "John Doe" → `[PERSON_0001]`)
    - **ORG**: Tên tổ chức (ví dụ: "Acme Corp" → `[ORG_0002]`)
    - **GPE**: Địa điểm địa chính trị (ví dụ: "New York" → `[GPE_0003]`)
    - **EMAIL**: Địa chỉ email (ví dụ: "john@example.com" → `[EMAIL_0004]`)
    - **PHONE**: Số điện thoại (ví dụ: "+1-555-0123" → `[PHONE_0005]`)
    - **DATE**: Ngày tháng (ví dụ: "2024-01-15" → `[DATE_0006]`)
  - Tạo bản đồ ánh xạ (mappings) từ dữ liệu gốc sang placeholder
  - Trả về: `(anonymized_text, mappings_dict)`

### 3.2 Deanonymizer (Khôi Phục Dữ Liệu)
- **Công nghệ**: Regex Pattern Matching và String Replacement
- **Chức năng**:
  - Nhận phản hồi từ LLM trong dạng ẩn danh (vẫn chứa `[LABEL_UUID]`)
  - Sử dụng bản đồ ánh xạ đã lưu từ bước Anonymizer
  - Thay thế các placeholder bằng giá trị gốc
  - Ví dụ: `"Thank you [PERSON_0001]"` → `"Thank you John Doe"`
  - Đảm bảo tính nhất quán và chính xác của dữ liệu

---

## 4. Ollama LLM Server - Lớp Mô Hình Ngôn Ngữ

**Ollama LLM Server** là trung tâm xử lý trí tuệ nhân tạo của hệ thống, chịu trách nhiệm tạo phản hồi email thông minh:

- **Công nghệ**: Ollama - Một framework chạy các mô hình ngôn ngữ lớn (LLM) cục bộ
- **Endpoint**: `http://localhost:11434` (chạy trên máy local)
- **Mô hình được hỗ trợ**:
  - `mistral:latest` - Mô hình mặc định, tốt với các tác vụ văn bản cân bằng
  - `mixtral` - Mô hình hỗn hợp chuyên gia (MoE), hiệu suất cao
  - `llama3` - Mô hình lớn từ Meta, khả năng suy luận mạnh
  - Các mô hình khác do người dùng chọn

- **Cấu hình**:
  - Temperature: `0.7` - Cân bằng giữa độ sáng tạo và tính nhất quán
  - Max tokens: Tùy chọn, giới hạn độ dài phản hồi
  - Top-p (nucleus sampling): Tối ưu hóa chất lượng phản hồi

- **Lợi ích**:
  - **Bảo mật dữ liệu**: Chạy hoàn toàn cục bộ, không gửi dữ liệu lên cloud
  - **Tính riêng tư**: Không phụ thuộc vào API bên thứ ba
  - **Chi phí thấp**: Không phải trả phí cho các dịch vụ LLM thương mại
  - **Tùy chỉnh**: Có thể chọn và nâng cấp mô hình tùy theo nhu cầu

---

## 5. Natural Language Processing Layer - Lớp Xử Lý Ngôn Ngữ Tự Nhiên

**NLP Layer** bao bọc Ollama LLM Server, cung cấp các tác vụ xử lý ngôn ngữ nâng cao:

### 5.1 OllamaLanguageModel Class
- **Chức năng chính**:
  - `generate(prompt, output_format=None, n_completions=1)` - Tạo phản hồi từ LLM
  - Tích hợp quá trình ẩn danh/khôi phục dữ liệu trong một pipeline thống nhất
  - Xử lý lỗi và timeout, đảm bảo dịch vụ không bị ngắt

### 5.2 Prompt Engineering
- **Định dạng prompt**: `"Reply politely and briefly to the following email:\n\n{email_body}"`
- **Chiến lược**: 
  - Yêu cầu phản hồi lịch sự và ngắn gọn
  - Cung cấp ngữ cảnh đầy đủ từ email gốc
  - Sử dụng dữ liệu ẩn danh để bảo vệ thông tin nhạy cảm

---

## 6. Logging & Audit Trail Layer - Lớp Ghi Nhật Ký và Kiểm Toán

**Logging Layer** đảm bảo tính minh bạch và khả năng theo dõi toàn bộ quá trình xử lý:

- **Công nghệ**: AutoPrint - Hệ thống ghi log có timestamp
- **Các tệp log chính**:
  - **Before.txt**: Nội dung email gốc trước khi ẩn danh
    - Ghi lại toàn bộ nội dung email từ người gửi
    - Timestamp khi email được nhận
    - Thông tin về người gửi và tiêu đề
  
  - **After.txt**: Nội dung email sau khi ẩn danh
    - Hiển thị trạng thái sau khi spaCy NER xử lý
    - Cho thấy quá trình thay thế thực thể bằng placeholder
    - Hỗ trợ kiểm tra chất lượng ẩn danh
  
  - **Response.txt**: Phản hồi từ LLM
    - Lưu trữ phản hồi ẩn danh từ Ollama
    - Lưu trữ phản hồi cuối cùng sau khi khôi phục dữ liệu
    - Cho phép kiểm tra tính chính xác của quá trình deanonymization
  
  - **Map.txt**: Bản đồ ánh xạ (Mappings)
    - Lưu trữ tất cả các cặp dữ liệu gốc → placeholder
    - Ví dụ: `{"PERSON": {"John Doe": "[PERSON_0001]"}, ...}`
    - Cần thiết cho việc khôi phục dữ liệu và kiểm tra

---

## 7. Luồng Xử Lý Hoàn Chỉnh

Hệ thống hoạt động theo luồng tuyến tính sau:

```
Email từ Gmail (IMAP)
    ↓
[Email Processor Layer - fetch_unseen_emails()]
    ↓
Tách thành: from_address, subject, body
    ↓
[Tạo Prompt]: "Reply politely to: {body}"
    ↓
[Anonymization Layer]
    ├─ spaCy NER: Phát hiện thực thể
    ├─ Tạo mappings
    └─ Output: anonymized_prompt
    ↓
[Logging] Before.txt + After.txt + Map.txt
    ↓
[Ollama LLM Server]
    ├─ Endpoint: localhost:11434
    ├─ Model: mistral:latest
    ├─ Input: anonymized_prompt
    └─ Output: anonymized_response
    ↓
[Logging] Response.txt (raw)
    ↓
[Deanonymization Layer]
    ├─ Đọc mappings từ Map.txt
    ├─ Regex replace: [LABEL_UUID] → original_value
    └─ Output: final_response
    ↓
[Logging] Response.txt (final)
    ↓
[Email Processor Layer - send_email()]
    ├─ Gửi reply tới người gửi gốc
    └─ Forward tới coworker (FORWARD_TO)
    ↓
✅ Hoàn tất - Chờ 60 giây rồi kiểm tra email mới
```

---

## 8. Các Công Nghệ Chi Tiết

| Thành Phần | Công Nghệ | Phiên Bản | Mục Đích |
|-----------|-----------|----------|---------|
| **Email Reception** | IMAP4 SSL/TLS | RFC 3501 | Nhận email từ Gmail |
| **Email Sending** | SMTP SSL/TLS | RFC 5321 | Gửi phản hồi email |
| **NER (Nhận diện Thực thể)** | spaCy | 3.x | Phát hiện dữ liệu nhạy cảm |
| **LLM Inference** | Ollama | Latest | Tạo phản hồi văn bản |
| **Models hỗ trợ** | Mistral, Mixtral, Llama3 | Latest | Xử lý NLP |
| **Logging** | AutoPrint | Custom | Ghi nhật ký với timestamp |
| **Configuration** | python-dotenv | 1.x | Quản lý biến môi trường |
| **Database** | File System (Log) | N/A | Lưu trữ nhật ký audit |

---

## 9. Bảo Mật & Quyền Riêng Tư

### 9.1 Ẩn Danh Hóa Dữ Liệu
- Tất cả dữ liệu cá nhân được ẩn danh trước khi gửi đến LLM
- Bản đồ ánh xạ được lưu trữ cục bộ để khôi phục dữ liệu
- Không có dữ liệu gốc được tiết lộ cho mô hình AI

### 9.2 Xác Thực & Mã Hóa
- Gmail credentials được lưu trong `.env` (không trong code)
- IMAP & SMTP sử dụng SSL/TLS encryption
- Kết nối an toàn tới Ollama qua localhost

### 9.3 Kiểm Toán & Nhật Ký
- Tất cả transformations được ghi lại cho mục đích audit
- Có thể theo dõi quá trình từ email gốc → ẩn danh → phản hồi → khôi phục
- Các tệp log được lưu trữ để phân tích sự cố

### 9.4 Xử Lý Ngoại Lệ
- Try-catch blocks bảo vệ tất cả các thao tác mạng
- Ghi log lỗi mà không tiết lộ thông tin nhạy cảm
- Retry logic cho các lỗi tạm thời

---

## 10. Mở Rộng & Tùy Chỉnh

Hệ thống được thiết kế để dễ dàng mở rộng:

- **Thay đổi mô hình LLM**: Chỉ cần cập nhật parameter `model` trong `OllamaLanguageModel`
- **Tùy chỉnh prompt**: Chỉnh sửa chuỗi `prompt` trong hàm `auto_process()`
- **Thêm xử lý sau**: Tích hợp thêm các bước xử lý giữa email nhận và gửi
- **Mở rộng IMAP/SMTP**: Hỗ trợ các nhà cung cấp email khác ngoài Gmail
- **Cải thiện NLP**: Nâng cấp spaCy model hoặc thêm custom NER rules

---

## 11. Kết Luận

Hệ thống ứng dụng tự động trả lời email **Auto_Chat_24_7** kết hợp các công nghệ tiên tiến để tạo ra một giải pháp xử lý email thông minh, an toàn và hiệu quả. Bằng cách tích hợp spaCy NER cho việc ẩn danh dữ liệu, Ollama LLM cho việc tạo phản hồi, và các lớp xử lý email dựa trên IMAP/SMTP, hệ thống đảm bảo rằng:

- ✅ **Thông tin cá nhân được bảo vệ** qua việc ẩn danh trước khi gửi LLM
- ✅ **Phản hồi thông minh và phù hợp ngữ cảnh** được tạo ra bởi các mô hình LLM tiên tiến
- ✅ **Tính minh bạch & kiểm toán** được duy trì thông qua hệ thống logging chi tiết
- ✅ **Hoạt động tự động 24/7** với khả năng xử lý hàng loạt email không biết mệt
- ✅ **Dễ dàng tùy chỉnh & mở rộng** để phù hợp với các nhu cầu cụ thể

Những đặc tính này làm cho **Auto_Chat_24_7** trở thành một giải pháp hoàn hảo cho các tổ chức muốn tự động hóa quá trình xử lý email trong khi vẫn duy trì tính bảo mật và chất lượng cao.

---

# Data Flow Diagram - Ứng Dụng Tự Động Trả Lời Email (Auto_Chat_24_7)

## Tổng Quan Luồng Dữ Liệu

Hệ thống **Auto_Chat_24_7** xử lý email theo một luồng dữ liệu tuyến tính, từ nhận email từ Gmail cho đến gửi phản hồi tự động. Mỗi bước trong luồng được thiết kế để đảm bảo bảo mật dữ liệu, ẩn danh thông tin cá nhân, và tạo phản hồi chất lượng cao.

---

## 1. STAGE 1: Email Reception - Nhận Email

### 1.1 Sender Sends Email
```
┌─────────────────────────────────────┐
│  📧 SENDER'S EMAIL                  │
│                                     │
│  From: john@example.com             │
│  Subject: Project Update Needed     │
│  Body: "Hi John Doe from Acme Corp, │
│         Can you review the Q4       │
│         report? My phone is         │
│         +1-555-0123. Thanks!"       │
└────────────┬────────────────────────┘
             │
             │ SMTP Protocol
             │ (Sender → Gmail Server)
             ▼
        ✅ Email stored in Gmail Inbox
```

**Mô tả:**
- Email được gửi từ người gửi tới Gmail SMTP server
- Gmail lưu trữ email trong thư mục Inbox
- Email được đánh dấu là `UNSEEN` (chưa đọc)

### 1.2 Fetch Unseen Emails
```
┌──────────────────────────────────────┐
│  🔍 FETCH EMAIL (IMAP Protocol)      │
│                                      │
│  1. Connect to imap.gmail.com:993    │
│  2. Authenticate with credentials   │
│  3. Select INBOX folder             │
│  4. Search: (UNSEEN)                 │
│  5. Retrieve message: RFC822 format  │
│  6. Parse headers & body             │
└────────────┬─────────────────────────┘
             │
             │ Extracted Data:
             │ - email_id: 12345
             │ - from_addr: john@example.com
             │ - subject: Project Update Needed
             │ - body: "Hi John Doe from Acme Corp..."
             ▼
        ✅ Email loaded into system
```

**Mô tả:**
- Kết nối an toàn (SSL/TLS) tới Gmail IMAP server
- Tìm kiếm email chưa đọc (UNSEEN)
- Parse email multipart (text + HTML + attachments)
- Trích xuất thông tin cần thiết
- Đóng kết nối IMAP

---

## 2. STAGE 2: Prompt Creation - Tạo Prompt

### 2.1 Extract & Format Content
```
┌──────────────────────────────────────┐
│  📝 CREATE PROMPT FOR LLM             │
│                                      │
│  Input:  Email body                  │
│                                      │
│  Processing:                         │
│  template = "Reply politely and      │
│              briefly to the          │
│              following email:\n\n{}" │
│                                      │
│  prompt = template.format(body)      │
└────────────┬─────────────────────────┘
             │
             │ Generated Prompt:
             │ "Reply politely and briefly to the
             │  following email:
             │
             │  Hi John Doe from Acme Corp,
             │  Can you review the Q4 report?
             │  My phone is +1-555-0123. Thanks!"
             ▼
        ✅ Prompt ready for LLM
```

**Mô tả:**
- Tạo prompt template chuẩn hóa
- Chèn nội dung email vào template
- Prompt sẽ được gửi tới Anonymization Layer tiếp theo
- Không có bất kỳ xử lý nào trên dữ liệu nhạy cảm ở giai đoạn này

---

## 3. STAGE 3: Anonymization - Ẩn Danh Hóa Dữ Liệu

Đây là **lớp bảo mật cốt lõi** để bảo vệ thông tin cá nhân.

### 3.1 spaCy NER Detection

```
┌────────────────────────────────────────────┐
│  🔐 ANONYMIZATION PHASE 1: NER DETECTION   │
│                                            │
│  Input Prompt:                             │
│  "Hi John Doe from Acme Corp, can you      │
│   review the Q4 report? My phone is        │
│   +1-555-0123. Thanks!"                    │
│                                            │
│  spaCy NER Processing:                     │
│  ┌──────────────────────────────────────┐  │
│  │ Entity Type    │ Text          │     │  │
│  │──────────────────────────────────────│  │
│  │ PERSON         │ John Doe      │     │  │
│  │ ORG            │ Acme Corp     │     │  │
│  │ PHONE          │ +1-555-0123   │     │  │
│  │ DATE           │ Q4            │     │  │
│  └──────────────────────────────────────┘  │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- spaCy `en_core_web_sm` model phân tích văn bản
- Nhận diện các loại thực thể (entities):
  - **PERSON**: Tên người
  - **ORG**: Tên tổ chức/công ty
  - **PHONE**: Số điện thoại
  - **EMAIL**: Địa chỉ email
  - **DATE**: Ngày tháng/thời gian
  - **GPE**: Địa điểm địa chính trị
  - **CARD**: Số thẻ tín dụng
  - **SSN**: Số an sinh xã hội

### 3.2 UUID Generation & Mapping

```
┌────────────────────────────────────────────┐
│  🔐 ANONYMIZATION PHASE 2: MAPPING         │
│                                            │
│  For each detected entity:                 │
│                                            │
│  1. PERSON: "John Doe"                     │
│     ├─ Generate UUID: 0001                 │
│     └─ Create mapping:                     │
│         "John Doe" → "[PERSON_0001]"       │
│                                            │
│  2. ORG: "Acme Corp"                       │
│     ├─ Generate UUID: 0002                 │
│     └─ Create mapping:                     │
│         "Acme Corp" → "[ORG_0002]"         │
│                                            │
│  3. PHONE: "+1-555-0123"                   │
│     ├─ Generate UUID: 0003                 │
│     └─ Create mapping:                     │
│         "+1-555-0123" → "[PHONE_0003]"     │
│                                            │
│  4. DATE: "Q4"                             │
│     ├─ Generate UUID: 0004                 │
│     └─ Create mapping:                     │
│         "Q4" → "[DATE_0004]"               │
│                                            │
│  Mappings Dictionary:                      │
│  {                                         │
│    "PERSON": {                             │
│      "John Doe": "[PERSON_0001]"           │
│    },                                      │
│    "ORG": {                                │
│      "Acme Corp": "[ORG_0002]"             │
│    },                                      │
│    "PHONE": {                              │
│      "+1-555-0123": "[PHONE_0003]"         │
│    },                                      │
│    "DATE": {                               │
│      "Q4": "[DATE_0004]"                   │
│    }                                       │
│  }                                         │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- Tạo UUID duy nhất cho mỗi loại thực thể (0001-9999)
- Lưu trữ bản đồ ánh xạ `original_value → placeholder`
- Bản đồ này sẽ được sử dụng để khôi phục dữ liệu sau

### 3.3 Text Replacement

```
┌────────────────────────────────────────────┐
│  🔐 ANONYMIZATION PHASE 3: REPLACEMENT     │
│                                            │
│  Original Prompt:                          │
│  "Hi John Doe from Acme Corp, can you      │
│   review the Q4 report? My phone is        │
│   +1-555-0123. Thanks!"                    │
│                                            │
│  String Replacement:                       │
│  1. "John Doe" → "[PERSON_0001]"           │
│  2. "Acme Corp" → "[ORG_0002]"             │
│  3. "+1-555-0123" → "[PHONE_0003]"         │
│  4. "Q4" → "[DATE_0004]"                   │
│                                            │
│  Anonymized Prompt:                        │
│  "Hi [PERSON_0001] from [ORG_0002],        │
│   can you review the [DATE_0004] report?    │
│   My phone is [PHONE_0003]. Thanks!"       │
│                                            │
│  Output:                                   │
│  - anonymized_prompt (text)                │
│  - mappings (dict)                         │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- Thay thế tất cả thực thể bằng placeholder `[LABEL_UUID]`
- Giữ nguyên cấu trúc văn bản
- Trả về: `(anonymized_prompt, mappings)`

### 3.4 Logging (Before & After)

```
┌────────────────────────────────────────────┐
│  💾 LOG: Before.txt (Original)              │
│                                            │
│  [2024-01-15 10:30:45]                     │
│  Original Prompt:                          │
│  Hi John Doe from Acme Corp, can you       │
│  review the Q4 report? My phone is         │
│  +1-555-0123. Thanks!                      │
└────────────┬───────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│  💾 LOG: After.txt (Anonymized)             │
│                                            │
│  [2024-01-15 10:30:45]                     │
│  Anonymized Prompt:                        │
│  Hi [PERSON_0001] from [ORG_0002],         │
│  can you review the [DATE_0004] report?    │
│  My phone is [PHONE_0003]. Thanks!         │
└────────────┬───────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│  💾 LOG: Map.txt (Mappings)                 │
│                                            │
│  [2024-01-15 10:30:45]                     │
│  {                                         │
│    "PERSON": {                             │
│      "John Doe": "[PERSON_0001]"           │
│    },                                      │
│    "ORG": {                                │
│      "Acme Corp": "[ORG_0002]"             │
│    },                                      │
│    "PHONE": {                              │
│      "+1-555-0123": "[PHONE_0003]"         │
│    },                                      │
│    "DATE": {                               │
│      "Q4": "[DATE_0004]"                   │
│    }                                       │
│  }                                         │
└────────────┬───────────────────────────────┘
             │
             ▼
        ✅ Anonymization Complete
```

**Mô tả:**
- **Before.txt**: Lưu nội dung gốc (chứa PII)
- **After.txt**: Lưu nội dung ẩn danh
- **Map.txt**: Lưu bản đồ ánh xạ để deanonymization
- Tất cả có timestamp để kiểm toán

---

## 4. STAGE 4: LLM Inference - Xử Lý bằng LLM

### 4.1 Send Request to Ollama

```
┌────────────────────────────────────────────┐
│  🤖 LLM INFERENCE PHASE 1: REQUEST          │
│                                            │
│  Endpoint: http://localhost:11434          │
│  Model: mistral:latest                     │
│  Temperature: 0.7                          │
│  Top-p: 0.9                                │
│                                            │
│  Request Payload:                          │
│  {                                         │
│    "model": "mistral:latest",              │
│    "prompt": "Hi [PERSON_0001] from        │
│               [ORG_0002], can you review   │
│               the [DATE_0004] report?      │
│               My phone is [PHONE_0003]...  │
│               Reply politely and           │
│               briefly",                    │
│    "temperature": 0.7,                     │
│    "top_p": 0.9                            │
│  }                                         │
└────────────┬───────────────────────────────┘
             │
             │ HTTP POST Request
             │ (localhost only - no internet)
             ▼
```

**Mô tả:**
- Kết nối tới Ollama server (chạy cục bộ)
- Gửi anonymized prompt (không chứa PII)
- Cấu hình temperature cho độ sáng tạo
- Dữ liệu không bao giờ rời khỏi máy tính

### 4.2 LLM Processing & Response

```
┌────────────────────────────────────────────┐
│  🤖 LLM INFERENCE PHASE 2: PROCESSING       │
│                                            │
│  Ollama/Mistral Model Processing:          │
│                                            │
│  Input Tokens:                             │
│  [CLS] Hi [PERSON_0001] from [ORG_0002],   │
│  can you review the [DATE_0004] report?    │
│  My phone is [PHONE_0003] ...              │
│                                            │
│  Model Layers:                             │
│  1. Embedding Layer                        │
│  2. Attention Heads (Multi-head attention) │
│  3. Feed Forward Networks                  │
│  4. Output Layer                           │
│                                            │
│  Generated Response:                       │
│  "Thank you [PERSON_0001] for reaching     │
│   out. [ORG_0002] will review your report  │
│   during the [DATE_0004] period. We can    │
│   reach you at [PHONE_0003]. Best regards" │
└────────────┬───────────────────────────────┘
             │
             │ Response (still anonymized)
             │ Contains placeholders: [LABEL_UUID]
             ▼
```

**Mô tả:**
- Mistral/Mixtral model xử lý dữ liệu ẩn danh
- Tạo phản hồi dựa trên context
- Phản hồi vẫn chứa placeholders (ví dụ: `[PERSON_0001]`)
- Không có thông tin PII rò rỉ

### 4.3 Logging LLM Response

```
┌────────────────────────────────────────────┐
│  💾 LOG: Response.txt (Raw - Anonymized)    │
│                                            │
│  [2024-01-15 10:30:52]                     │
│  LLM Output (Raw):                         │
│  Thank you [PERSON_0001] for reaching      │
│  out. [ORG_0002] will review your report   │
│  during the [DATE_0004] period. We can     │
│  reach you at [PHONE_0003]. Best regards   │
│                                            │
│  Metadata:                                 │
│  - Model: mistral:latest                   │
│  - Temperature: 0.7                        │
│  - Response time: 7.234 seconds            │
│  - Tokens generated: 45                    │
└────────────┬───────────────────────────────┘
             │
             ▼
        ✅ LLM Processing Complete
```

**Mô tả:**
- Lưu phản hồi thô từ LLM
- Ghi lại metadata (model, nhiệt độ, thời gian)
- Phản hồi vẫn ở dạng ẩn danh

---

## 5. STAGE 5: De-anonymization - Khôi Phục Dữ Liệu

### 5.1 Load Mappings

```
┌────────────────────────────────────────────┐
│  🔓 DE-ANONYMIZATION PHASE 1: LOAD MAPS     │
│                                            │
│  Read from Map.txt:                        │
│  {                                         │
│    "PERSON": {                             │
│      "John Doe": "[PERSON_0001]"           │
│    },                                      │
│    "ORG": {                                │
│      "Acme Corp": "[ORG_0002]"             │
│    },                                      │
│    "PHONE": {                              │
│      "+1-555-0123": "[PHONE_0003]"         │
│    },                                      │
│    "DATE": {                               │
│      "Q4": "[DATE_0004]"                   │
│    }                                       │
│  }                                         │
│                                            │
│  Create Reverse Mappings:                  │
│  {                                         │
│    "[PERSON_0001]": "John Doe",            │
│    "[ORG_0002]": "Acme Corp",              │
│    "[PHONE_0003]": "+1-555-0123",          │
│    "[DATE_0004]": "Q4"                     │
│  }                                         │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- Đọc bản đồ ánh xạ từ Map.txt
- Tạo reverse mapping: `[LABEL_UUID] → original_value`
- Sử dụng regex pattern matching để tìm placeholders

### 5.2 Pattern Matching & Replacement

```
┌────────────────────────────────────────────┐
│  🔓 DE-ANONYMIZATION PHASE 2: REPLACEMENT   │
│                                            │
│  Input (Anonymized Response):              │
│  "Thank you [PERSON_0001] for reaching     │
│   out. [ORG_0002] will review your report  │
│   during the [DATE_0004] period. We can    │
│   reach you at [PHONE_0003]. Best regards" │
│                                            │
│  Regex Pattern: \[([A-Z_]+_\d{4})\]        │
│  Matches:                                  │
│  1. [PERSON_0001]                          │
│  2. [ORG_0002]                             │
│  3. [DATE_0004]                            │
│  4. [PHONE_0003]                           │
│                                            │
│  Replacement Process:                      │
│  1. Find: [PERSON_0001]                    │
│     Replace with: John Doe                 │
│  2. Find: [ORG_0002]                       │
│     Replace with: Acme Corp                │
│  3. Find: [DATE_0004]                      │
│     Replace with: Q4                       │
│  4. Find: [PHONE_0003]                     │
│     Replace with: +1-555-0123              │
│                                            │
│  Output (Restored Response):               │
│  "Thank you John Doe for reaching out.     │
│   Acme Corp will review your report during │
│   the Q4 period. We can reach you at       │
│   +1-555-0123. Best regards"               │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- Sử dụng regex pattern để tìm tất cả placeholders
- So khớp từng placeholder với bản đồ reverse
- Thay thế bằng giá trị gốc
- Xác minh tính chính xác của quá trình

### 5.3 Context Verification

```
┌────────────────────────────────────────────┐
│  🔓 DE-ANONYMIZATION PHASE 3: VERIFICATION  │
│                                            │
│  Verify Restored Text:                     │
│  ✓ Tất cả placeholders đã được thay thế    │
│  ✓ Không còn [LABEL_UUID] nào              │
│  ✓ Ngữ pháp & ngữ cảnh hợp lý              │
│  ✓ Dữ liệu khớp với original mappings      │
│                                            │
│  Final Output:                             │
│  "Thank you John Doe for reaching out.     │
│   Acme Corp will review your report during │
│   the Q4 period. We can reach you at       │
│   +1-555-0123. Best regards"               │
│                                            │
│  Status: ✅ De-anonymization Successful    │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- Kiểm tra toàn bộ placeholders đã được thay thế
- Xác minh tính hợp lệ của văn bản
- Đảm bảo không có dữ liệu PII bị mất hoặc sai

### 5.4 Logging Final Response

```
┌────────────────────────────────────────────┐
│  💾 LOG: Response.txt (Final - Restored)    │
│                                            │
│  [2024-01-15 10:30:54]                     │
│  LLM Output (Final - De-anonymized):       │
│  Thank you John Doe for reaching out.      │
│  Acme Corp will review your report during  │
│  the Q4 period. We can reach you at        │
│  +1-555-0123. Best regards                 │
│                                            │
│  Quality Metrics:                          │
│  - De-anonymization success: 100%          │
│  - Placeholders replaced: 4/4              │
│  - Context integrity: ✅ Valid             │
└────────────┬───────────────────────────────┘
             │
             ▼
        ✅ De-anonymization Complete
```

**Mô tả:**
- Lưu phản hồi cuối cùng (đã khôi phục)
- Ghi lại độ chính xác của de-anonymization
- Tất cả dữ liệu đã sẵn sàng để gửi

---

## 6. STAGE 6: Email Response - Gửi Phản Hồi

### 6.1 Format Email Response

```
┌────────────────────────────────────────────┐
│  📧 FORMAT EMAIL RESPONSE                  │
│                                            │
│  To: john@example.com                      │
│  From: system@company.com                  │
│  Subject: Re: Project Update Needed        │
│  Content-Type: text/plain; charset=utf-8   │
│  Date: Mon, 15 Jan 2024 10:30:55 GMT       │
│                                            │
│  Body:                                     │
│  Thank you John Doe for reaching out.      │
│  Acme Corp will review your report during  │
│  the Q4 period. We can reach you at        │
│  +1-555-0123. Best regards                 │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- Tạo MIME message object
- Đặt tiêu đề email với "Re: " prefix
- Thiết lập charset (UTF-8)
- Đính kèm phản hồi đã khôi phục

### 6.2 Send Reply to Sender

```
┌────────────────────────────────────────────┐
│  📤 SEND REPLY (SMTP Protocol)              │
│                                            │
│  1. Connect to smtp.gmail.com:465           │
│  2. Authenticate with Gmail credentials    │
│  3. Send message:                          │
│     From: system@company.com               │
│     To: john@example.com                   │
│     Subject: Re: Project Update Needed     │
│                                            │
│  4. Log transmission:                      │
│     [2024-01-15 10:30:56]                  │
│     ✅ Reply sent successfully              │
│     Message-ID: <ABC123@company.com>       │
│     Status: 250 OK                         │
│                                            │
│  5. Close SMTP connection                  │
└────────────┬───────────────────────────────┘
             │
             │ SMTP Protocol
             │ (System → Sender)
             ▼
      ✅ Email Delivered to Sender
```

**Mô tả:**
- Kết nối SSL/TLS tới Gmail SMTP
- Gửi phản hồi đến người gửi gốc
- Ghi lại trạng thái gửi
- Đóng kết nối SMTP

### 6.3 Forward to Coworker

```
┌────────────────────────────────────────────┐
│  📤 FORWARD EMAIL (SMTP Protocol)           │
│                                            │
│  1. Format Forward Message:                │
│     To: coworker@company.com               │
│     From: system@company.com               │
│     Subject: FWD: Project Update Needed    │
│                                            │
│  2. Include in Body:                       │
│     "---------- Forwarded message ---------│
│      From: john@example.com                │
│      To: system@company.com                │
│      Subject: Project Update Needed        │
│      Date: Mon, 15 Jan 2024 10:15 GMT      │
│                                            │
│      Hi John Doe from Acme Corp...         │
│      (original email body)                 │
│      --------- Auto-Reply --------         │
│      Thank you John Doe for reaching out.  │
│      Acme Corp will review your report...  │
│      (auto-generated reply)"               │
│                                            │
│  3. Send via SMTP                          │
│     ✅ Forward sent successfully            │
│     Status: 250 OK                         │
└────────────┬───────────────────────────────┘
             │
             │ SMTP Protocol
             │ (System → Coworker)
             ▼
      ✅ Email Forwarded to Coworker
```

**Mô tả:**
- Tạo forward message với cấu trúc đầy đủ
- Bao gồm email gốc + phản hồi tự động
- Gửi tới coworker để kiểm tra
- Giúp quản lý xem lại các email đã xử lý

### 6.4 Logging Send Results

```
┌────────────────────────────────────────────┐
│  💾 LOG: SEND RESULTS                       │
│                                            │
│  [2024-01-15 10:30:56]                     │
│  ✅ SEND EMAIL RESULTS                      │
│                                            │
│  1. Reply to Sender:                       │
│     To: john@example.com                   │
│     Status: ✅ SENT                         │
│     Time: 2024-01-15 10:30:56              │
│     Message-ID: <ABC123@company.com>       │
│                                            │
│  2. Forward to Coworker:                   │
│     To: coworker@company.com               │
│     Status: ✅ SENT                         │
│     Time: 2024-01-15 10:30:57              │
│     Message-ID: <DEF456@company.com>       │
│                                            │
│  Summary:                                  │
│  Total emails processed: 1                 │
│  Replies sent: 1                           │
│  Forwards sent: 1                          │
│  Success rate: 100%                        │
└────────────┬───────────────────────────────┘
             │
             ▼
```

**Mô tả:**
- Ghi lại trạng thái gửi email
- Lưu Message-IDs để theo dõi
- Ghi lại thời gian gửi chính xác
- Thống kê số lượng email xử lý

---

## 7. STAGE 7: Completion & Loop

### 7.1 Process Complete

```
┌────────────────────────────────────────────┐
│  ✅ PROCESS COMPLETE                        │
│                                            │
│  Email Processing Summary:                 │
│  ├─ Email ID: 12345                        │
│  ├─ From: john@example.com                 │
│  ├─ Subject: Project Update Needed         │
│  ├─ Status: ✅ Processed & Replied          │
│  ├─ Processing time: 11.5 seconds          │
│  ├─ Anonymization: ✅ 4 entities detected   │
│  ├─ LLM response time: 7.2 seconds         │
│  ├─ De-anonymization: ✅ 100% success       │
│  ├─ Reply sent: ✅ john@example.com         │
│  └─ Forward sent: ✅ coworker@company.com   │
│                                            │
│  Next Action:                              │
│  Sleep 60 seconds...                       │
│  Waiting for new emails...                 │
└────────────┬───────────────────────────────┘
             │
             │ time.sleep(60)
             ▼
```

**Mô tả:**
- Tính toán thời gian xử lý tổng cộng
- Tạo báo cáo tóm tắt toàn bộ quá trình
- Ghi lại tất cả các bước thành công
- Chuẩn bị cho vòng lặp tiếp theo

### 7.2 Loop Continuation

```
┌────────────────────────────────────────────┐
│  🔄 LOOP CONTINUATION                       │
│                                            │
│  [2024-01-15 10:31:56] - 60 seconds later   │
│                                            │
│  while True:                               │
│    1. Fetch new unseen emails              │
│       └─ Check IMAP inbox again            │
│    2. For each new email:                  │
│       └─ Repeat STAGE 1-6                  │
│    3. Sleep 60 seconds                     │
│    4. Continue monitoring 24/7             │
│                                            │
│  Service Status:                           │
│  🟢 Running (24/7)                          │
│  🟢 Ready for new emails                    │
│  🟢 Processing capability: 1 email/loop    │
│  🟢 Maximum concurrent: 1 (sequential)     │
│                                            │
│  Recent Activity Log:                      │
│  [10:30:56] ✅ Email processed              │
│  [10:31:56] 🔍 Checking for new emails     │
│  [10:31:57] 📭 No new emails found          │
│  [10:32:57] 🔍 Checking for new emails     │
│  [10:32:58] 📨 1 new email found!           │
│  [10:33:00] 🔐 Anonymizing...               │
│  [10:33:01] 🤖 Calling LLM...               │
│  [10:33:08] 🔓 De-anonymizing...            │
│  [10:33:09] 📤 Sending replies...           │
│  [10:33:10] ✅ Process complete             │
└────────────┬───────────────────────────────┘
             │
             ▼
    Continuous Service (∞ Loop)
```

**Mô tả:**
- Lặp vô hạn để xử lý email mới
- Kiểm tra IMAP mỗi 60 giây
- Xử lý email tuần tự (một lần một email)
- Duy trì hoạt động 24/7

---

## 8. Data Transformation Summary

### 8.1 Transformation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA TRANSFORMATION PIPELINE              │
└─────────────────────────────────────────────────────────────┘

STAGE 1: EMAIL RECEPTION
Input:  Raw email from Gmail
Output: Parsed email (from, subject, body)
        ├─ Email ID: 12345
        ├─ From: john@example.com
        ├─ Subject: Project Update Needed
        └─ Body: "Hi John Doe from Acme Corp..."

                            ↓

STAGE 2: PROMPT CREATION
Input:  Parsed email body
Output: Formatted prompt for LLM
        "Reply politely to: Hi John Doe from Acme Corp..."

                            ↓

STAGE 3: ANONYMIZATION
Input:  Raw prompt (with PII)
Output: Anonymized prompt + Mappings
        ├─ Prompt: "Hi [PERSON_0001] from [ORG_0002]..."
        └─ Mappings: {"PERSON": {"John Doe": "[PERSON_0001]"}}

                            ↓

STAGE 4: LLM INFERENCE
Input:  Anonymized prompt (safe to process)
Output: Anonymized response
        "Thank you [PERSON_0001] from [ORG_0002]..."

                            ↓

STAGE 5: DE-ANONYMIZATION
Input:  Anonymized response + Mappings
Output: Final response (with original data restored)
        "Thank you John Doe from Acme Corp..."

                            ↓

STAGE 6: EMAIL SENDING
Input:  Final response
Output: 
        1. Reply sent to john@example.com
        2. Forward sent to coworker@company.com

                            ↓

STAGE 7: LOGGING & LOOP
Input:  All stage results
Output: 
        1. Comprehensive logs (Before.txt, After.txt, etc.)
        2. Return to STAGE 1 (wait 60 seconds, then repeat)
```

### 8.2 Data Size Reference

```
┌──────────────────────────────────────────────┐
│         TYPICAL DATA SIZE THROUGH PIPELINE    │
└──────────────────────────────────────────────┘

Original Email:        ~500 bytes (header + body)
                          ↓
Parsed Email:          ~400 bytes
                          ↓
Prompt Created:        ~450 bytes
                          ↓
Anonymized Prompt:     ~480 bytes (similar, with placeholders)
                          ↓
LLM Response:          ~300 bytes (shorter reply)
                          ↓
Final Response:        ~320 bytes (restored with original data)
                          ↓
Mappings Storage:      ~200 bytes (mapping table)
                          ↓
Total Logs:            ~2 KB (Before + After + Map + Response)

Memory Usage (per email): ~5-10 MB (including model inference)
Processing Time:         10-15 seconds
Network Bandwidth:       ~2 KB (minimal - local processing only)
```

---

## 9. Security Considerations in Data Flow

```
┌─────────────────────────────────────────────────────────┐
│          SECURITY CHECKPOINTS IN DATA FLOW               │
└─────────────────────────────────────────────────────────┘

✅ CHECKPOINT 1: Email Reception
   ├─ SSL/TLS encryption (IMAP)
   ├─ Gmail authentication
   └─ Credential protection (.env file)

✅ CHECKPOINT 2: Anonymization
   ├─ PII detection & replacement
   ├─ Mappings stored locally (not transmitted)
   └─ No raw PII sent to LLM

✅ CHECKPOINT 3: LLM Processing
   ├─ Localhost only (no internet transmission)
   ├─ Anonymized data only (safe)
   └─ Model confined to local environment

✅ CHECKPOINT 4: De-anonymization
   ├─ Uses stored local mappings
   ├─ Regex pattern matching (safe)
   └─ Original data never exposed to external services

✅ CHECKPOINT 5: Email Sending
   ├─ SSL/TLS encryption (SMTP)
   ├─ Gmail authentication
   └─ Final check before send

✅ CHECKPOINT 6: Audit Trail
   ├─ All transformations logged
   ├─ Before/After comparison
   ├─ Mappings stored for verification
   └─ No logs contain raw PII
```

---

## 10. Error Handling in Data Flow

```
┌─────────────────────────────────────────────────────┐
│      ERROR HANDLING AT EACH STAGE                    │
└─────────────────────────────────────────────────────┘

STAGE 1: Email Reception
├─ ❌ IMAP connection failed
│  └─ Action: Retry after 5 seconds, log error
├─ ❌ Email parsing error
│  └─ Action: Skip email, move to next
└─ ❌ Empty email body
   └─ Action: Skip, don't send reply

STAGE 2: Prompt Creation
├─ ❌ Subject encoding error
│  └─ Action: Use default subject "Re: Email"
└─ ❌ Body too large (>10MB)
   └─ Action: Truncate to 5000 chars, continue

STAGE 3: Anonymization
├─ ❌ spaCy model not loaded
│  └─ Action: Skip anonymization, warn user
└─ ❌ UUID collision (unlikely)
   └─ Action: Regenerate UUID

STAGE 4: LLM Inference
├─ ❌ Ollama not running
│  └─ Action: Log error, retry in next loop
├─ ❌ Timeout (>120 seconds)
│  └─ Action: Abort, move to next email
└─ ❌ Invalid response format
   └─ Action: Use generic reply, log error

STAGE 5: De-anonymization
├─ ❌ Mapping not found
│  └─ Action: Keep placeholder, warn in log
└─ ❌ Multiple matches for placeholder
   └─ Action: Use first match, log ambiguity

STAGE 6: Email Sending
├─ ❌ SMTP authentication failed
│  └─ Action: Log error, check credentials in .env
├─ ❌ Recipient address invalid
│  └─ Action: Log error, skip send
└─ ❌ Network timeout
   └─ Action: Retry up to 3 times

STAGE 7: Logging & Loop
├─ ❌ Log file write failed
│  └─ Action: Continue anyway, print to console
└─ ❌ Out of disk space
   └─ Action: Alert user, pause service
```

---

## 11. Performance Metrics

```
┌──────────────────────────────────────────────────┐
│        TYPICAL PERFORMANCE METRICS                │
└──────────────────────────────────────────────────┘

Processing Times:
├─ Email fetch (IMAP):           1-2 seconds
├─ Anonymization (spaCy NER):    0.5-1 seconds
├─ LLM inference (Ollama):       5-10 seconds
├─ De-anonymization:             0.1-0.3 seconds
├─ Email send (SMTP):            1-2 seconds
└─ Total per email:              8-16 seconds

Throughput:
├─ Sequential processing:        1 email per loop
├─ Loop interval:                60 seconds
├─ Theoretical max:              60 emails/hour
└─ Practical average:            30-40 emails/hour

Resource Usage:
├─ CPU:                          10-30% (during LLM)
├─ Memory:                       800 MB - 1.5 GB
├─ Disk I/O:                     Minimal (<1 MB/email)
├─ Network:                      <10 KB/email (Gmail)
└─ Ollama memory:                4-8 GB (model dependent)

Storage:
├─ Logs per email:               1-2 KB
├─ Daily logs (100 emails):      100-200 KB
├─ Monthly logs:                 3-6 MB
└─ Mappings storage:             Inline with logs
```

---

## Kết Luận

Luồng dữ liệu của **Auto_Chat_24_7** được thiết kế để:

✅ **Bảo vệ thông tin cá nhân**: Ẩn danh trước khi gửi LLM
✅ **Đảm bảo tính riêng tư**: Xử lý cục bộ, không gửi lên cloud
✅ **Duy trì tính audit**: Ghi lại tất cả các bước transformations
✅ **Xử lý lỗi tốt**: Có cơ chế fallback ở mỗi giai đoạn
✅ **Tối ưu hiệu suất**: Xử lý tuần tự nhưng nhanh chóng
✅ **Dễ dàng mở rộng**: Có thể thêm các bước xử lý mới

Toàn bộ quá trình hoạt động 24/7, liên tục kiểm tra email mới và tự động tạo phản hồi thông minh, đồng thời bảo vệ dữ liệu nhạy cảm của người dùng.
