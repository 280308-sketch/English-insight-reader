import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI

app = FastAPI()

# Thay thế đoạn trong ngoặc bằng API Key của bạn hoặc cấu hình biến môi trường
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Giao diện HTML di động tích hợp sẵn (2 chế độ Academic và Quick Fact)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>English AI Reader</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        h2 { color: #2c3e50; text-align: center; }
        .tabs { display: flex; justify-content: center; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; border: none; background: #ddd; margin: 0 5px; border-radius: 6px; font-weight: bold; }
        .tab.active { background: #3498db; color: white; }
        .content-box { background: #f9f9f9; padding: 15px; border-left: 4px solid #3498db; border-radius: 4px; margin-bottom: 15px; line-height: 1.6; }
        textarea { width: 100%; height: 120px; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 16px; margin-bottom: 15px; }
        button.submit-btn { width: 100%; background: #2ecc71; color: white; border: none; padding: 12px; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button.submit-btn:hover { background: #27ae60; }
        .result { margin-top: 20px; padding: 15px; background: #e8f8f5; border-radius: 6px; border: 1px solid #a3e4d7; }
    </style>
</head>
<body>
<div class="container">
    <h2>English Reading AI</h2>
    
    <!-- Chọn Chế độ -->
    <div class="tabs">
        <button class="tab active" onclick="setMode('academic')">Academic (Đoạn dài)</button>
        <button class="tab" onclick="setMode('quick')">Quick Fact (Lướt web)</button>
    </div>

    <form method="post" action="/evaluate">
        <input type="hidden" name="mode" id="modeInput" value="academic">
        
        <p><b>Đoạn văn tiếng Anh cần đọc:</b></p>
        <div class="content-box">
            {{ current_text }}
        </div>
        <input type="hidden" name="english_text" value="{{ current_text }}">

        <p><b>Bạn hiểu đoạn này thế nào? (Nhập bằng tiếng Việt):</b></p>
        <textarea name="user_response" placeholder="Viết tóm tắt hoặc ý chính theo hiểu biết của bạn..." required></textarea>
        
        <button type="submit" class="submit-btn">Gửi AI Đánh Giá</button>
    </form>

    {% if evaluation %}
    <div class="result">
        <h3>Kết quả đánh giá từ AI:</h3>
        <p>{{ evaluation | safe }}</p>
    </div>
    {% endif %}
</div>

<script>
    function setMode(mode) {
        document.getElementById('modeInput').value = mode;
        // Chuyển hướng hoặc tải lại với mode tương ứng (có thể tối ưu thêm bằng JS, tạm thời để form xử lý đơn giản)
        window.location.href = "/?mode=" + mode;
    }
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home(mode: str = "academic"):
    # Mẫu dữ liệu tạm thời (sau này bạn có thể cho AI tự động sinh đoạn văn từ API)
    if mode == "quick":
        sample_text = "The tongue map is a long-standing scientific myth. Different areas of the human tongue can perceive all basic tastes roughly equally, rather than specialized regions for sweet, salty, sour, and bitter."
    else:
        sample_text = "Neuroplasticity refers to the brain's ability to reorganize itself by forming new neural connections throughout life. This dynamic process allows the neurons in the brain to compensate for injury and disease and to adjust their activities in response to new situations or to changes in the environment."
    
    return HTMLResponse(content=HTML_TEMPLATE.replace("{{ current_text }}", sample_text).replace("{{ evaluation }}", ""))

@app.post("/evaluate", response_class=HTMLResponse)
async def evaluate(mode: str = Form(...), english_text: str = Form(...), user_response: str = Form(...)):
    try:
        prompt = f"""
        Bạn là một giảng viên tiếng Anh và chuyên gia phân tích nội dung. 
        Đoạn văn gốc tiếng Anh: "{english_text}"
        Phản hồi bằng tiếng Việt của người dùng về ý nghĩa đoạn văn: "{user_response}"
        
        Hãy đánh giá xem người dùng đã hiểu đúng ý chính hay chưa, chỉ ra các điểm họ hiểu tốt, và bổ sung những ý quan trọng mà họ còn thiếu sót. Trình bày ngắn gọn, súc tích, bằng tiếng Việt.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        eval_result = response.choices[0].message.content.replace('\n', '<br>')
    except Exception as e:
        # Nếu có lỗi (sai key, hết tiền, mất mạng), hiển thị chi tiết lỗi màu đỏ lên giao diện
        eval_result = f"<b style='color: red;'>Lỗi kết nối AI:</b> {str(e)}"
    
    rendered = HTML_TEMPLATE.replace("{{ current_text }}", english_text).replace("{{ evaluation }}", eval_result)
    return HTMLResponse(content=rendered)